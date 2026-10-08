// ROS 2 node: the C++ FGO live (the counterpart of src/estimators/fgo/fgo_node.py). A THIN shell around
// fgo_cpp::LiveAdapter, the class the offline bag-replay harness (fgo_cpp_live_replay) drives.
//
// Subscriptions (as fgo_node.py): /imu/data_raw, /imu/time_ref, /optical_flow/measurement, /downward_lidar/range,
// /attitude/angular_rates; /forward_camera/heading_sent if heading:=true; /tags/sent if tags:=true.
// Callbacks only copy each message into a queue (arrival order); a worker thread feeds the adapter, so the executor
// never blocks on a keyframe solve (the fgo_node.py history: blocking callbacks lost ~1.4% of IMU messages).
// Publishes /fgo/pose (PoseStamped, navigation frame, keyframe stamp) and /fgo/valid (Bool) per keyframe, and sends
// ODOMETRY (LOCAL_NED, MAV_ESTIMATOR_TYPE_NAIVE, quality 100/0) to ArduPilot over mavlink_out (pymavlink "udp:"
// listen semantics: replies to SITL SERIAL3's udpclient), reading the autopilot's HEARTBEAT armed flag from the same
// socket for the ground-proximity rule's arming time.
//
// Parameters: reorder_delay_s (0.20), imu_stamp (time_ref|causal|header), window_s (0.25), lm_iters (2),
// heading (false), heading_sigma_deg (5), tags (false), nav_frame (corridor|enu), mavlink_out (""),
// arm_source (heartbeat|none), gap_rule (true).
#include <atomic>
#include <chrono>
#include <cstdio>
#include <cmath>
#include <condition_variable>
#include <deque>
#include <mutex>
#include <thread>
#include <variant>

#include <geometry_msgs/msg/pose_stamped.hpp>
#include <geometry_msgs/msg/pose_with_covariance_stamped.hpp>
#include <geometry_msgs/msg/vector3_stamped.hpp>
#include <optical_flow_interfaces/msg/optical_flow.hpp>
#include <rclcpp/rclcpp.hpp>
#include <sensor_msgs/msg/imu.hpp>
#include <sensor_msgs/msg/range.hpp>
#include <sensor_msgs/msg/time_reference.hpp>
#include <std_msgs/msg/bool.hpp>

#include "fgo_cpp/live_adapter.h"

using fgo_cpp::Vector3;

namespace {
double st(const builtin_interfaces::msg::Time& t) { return t.sec + t.nanosec * 1e-9; }
std::string jnum(double x) {   // a JSON number, or null for NaN (time_ref fields in causal/header mode)
  if (!std::isfinite(x)) return "null";
  char b[64];
  std::snprintf(b, sizeof b, "%.6f", x);
  return b;
}

struct Msg {   // one arrival, copied out of the callback
  int kind;    // tape kinds (fgo_live_replay.cpp): 0 imu, 1 att, 2 rng, 3 flow, 4 heading, 5 tag, 7 time_ref
  double t;
  double v[8];
  std::chrono::steady_clock::time_point wall;   // arrival (callback) time, for the queue lag
};
}  // namespace

class FgoCppNode : public rclcpp::Node {
 public:
  FgoCppNode() : Node("fgo_cpp_node") {
    fgo_cpp::LiveConfig cfg;
    cfg.base.mode = declare_parameter("tags", false) ? "room" : "corridor";
    cfg.base.window = declare_parameter("window_s", 0.25);
    cfg.base.lm_iters = static_cast<int>(declare_parameter("lm_iters", 2));
    cfg.base.kf_dt = 1.0 / 30.0;
    cfg.base.tag_sigma_pos = declare_parameter("tag_sigma_pos", 0.05);
    cfg.base.tag_sigma_yaw = declare_parameter("tag_sigma_yaw_deg", 5.0) * M_PI / 180.0;
    cfg.reorder_delay = declare_parameter("reorder_delay_s", 0.20);
    cfg.imu_stamp = declare_parameter("imu_stamp", std::string("time_ref"));
    cfg.heading = declare_parameter("heading", false);
    cfg.heading_sigma = declare_parameter("heading_sigma_deg", 5.0) * M_PI / 180.0;
    cfg.nav_frame = declare_parameter("nav_frame", std::string(cfg.base.mode == "room" ? "enu" : "corridor"));
    cfg.arm_source = declare_parameter("arm_source", std::string("heartbeat"));
    cfg.gap_rule = declare_parameter("gap_rule", true);
    const std::string out = declare_parameter("mavlink_out", std::string(""));
    stats_path_ = declare_parameter("stats_path", std::string(""));   // on shutdown: <path>.f64 + <path>.json
    cfg_desc_ = "reorder_delay_s=" + std::to_string(cfg.reorder_delay) + " imu_stamp=" + cfg.imu_stamp +
                " arm_source=" + cfg.arm_source + " heading=" + (cfg.heading ? "true" : "false");
    RCLCPP_INFO(get_logger(), "fgo_cpp_node: %s mavlink_out=%s", cfg_desc_.c_str(), out.c_str());
    if (!out.empty()) {
      udp_.reset(new fgo_cpp::mav::UdpEndpoint(out));
      if (!udp_->ok()) RCLCPP_ERROR(get_logger(), "cannot bind %s", out.c_str());
    }
    pub_ = create_publisher<geometry_msgs::msg::PoseStamped>("/fgo/pose", 10);
    pub_valid_ = create_publisher<std_msgs::msg::Bool>("/fgo/valid", 10);
    adapter_.reset(new fgo_cpp::LiveAdapter(cfg, [this](const fgo_cpp::LiveOutput& o) { output(o); }));

    const auto q = rclcpp::QoS(rclcpp::KeepLast(200)).reliable();
    subs_.push_back(create_subscription<sensor_msgs::msg::Imu>("/imu/data_raw", q, [this](sensor_msgs::msg::Imu::ConstSharedPtr m) {
      enqueue({0, st(m->header.stamp), {m->linear_acceleration.x, m->linear_acceleration.y, m->linear_acceleration.z,
                                        m->angular_velocity.x, m->angular_velocity.y, m->angular_velocity.z}});
    }));
    subs_.push_back(create_subscription<sensor_msgs::msg::TimeReference>("/imu/time_ref", q,
        [this](sensor_msgs::msg::TimeReference::ConstSharedPtr m) { enqueue({7, st(m->header.stamp), {st(m->time_ref)}}); }));
    subs_.push_back(create_subscription<optical_flow_interfaces::msg::OpticalFlow>("/optical_flow/measurement", q,
        [this](optical_flow_interfaces::msg::OpticalFlow::ConstSharedPtr m) {
          enqueue({3, st(m->header.stamp), {m->flow_x_rad, m->flow_y_rad, m->valid ? 1.0 : 0.0, m->inlier_ratio}});
        }));
    subs_.push_back(create_subscription<sensor_msgs::msg::Range>("/downward_lidar/range", q,
        [this](sensor_msgs::msg::Range::ConstSharedPtr m) { enqueue({2, st(m->header.stamp), {m->range}}); }));
    subs_.push_back(create_subscription<geometry_msgs::msg::Vector3Stamped>("/attitude/angular_rates", q,
        [this](geometry_msgs::msg::Vector3Stamped::ConstSharedPtr m) {
          enqueue({1, st(m->header.stamp), {m->vector.x, m->vector.y, m->vector.z}});
        }));
    if (cfg.heading)
      subs_.push_back(create_subscription<geometry_msgs::msg::Vector3Stamped>("/forward_camera/heading_sent", q,
          [this](geometry_msgs::msg::Vector3Stamped::ConstSharedPtr m) {
            enqueue({4, st(m->header.stamp), {m->vector.x, m->vector.y, m->vector.z}});   // NED yaw, quality, angErr
          }));
    if (cfg.base.mode == "room")
      subs_.push_back(create_subscription<geometry_msgs::msg::PoseWithCovarianceStamped>("/tags/sent", q,
          [this](geometry_msgs::msg::PoseWithCovarianceStamped::ConstSharedPtr m) {
            const auto& o = m->pose.pose.orientation;
            enqueue({5, st(m->header.stamp), {m->pose.pose.position.x, m->pose.pose.position.y, 2 * std::atan2(o.z, o.w)}});
          }));
    worker_ = std::thread([this] { run(); });
  }

  ~FgoCppNode() override {
    stop_ = true;
    cv_.notify_all();
    if (worker_.joinable()) worker_.join();
    // as fgo_node.py: drain what arrived before the stop, flush the reorder buffer, then write the stats
    std::deque<Msg> rest;
    {
      std::lock_guard<std::mutex> lk(mu_);
      rest.swap(q_);
    }
    for (const Msg& m : rest) feed(m);
    adapter_->flush();
    write_stats();
    RCLCPP_INFO(get_logger(), "keyframes sent %zu, unsettled %zu, reinits %zu, max lateness %.3f s, out-of-order %zu",
                adapter_->n_sent, adapter_->n_unsettled, adapter_->n_reinits, adapter_->max_lateness(), adapter_->n_out_of_order());
  }

 private:
  void enqueue(Msg m) {
    m.wall = std::chrono::steady_clock::now();
    {
      std::lock_guard<std::mutex> lk(mu_);
      q_.push_back(m);
    }
    cv_.notify_one();
  }

  void run() {
    while (!stop_) {
      std::deque<Msg> batch;
      {
        std::unique_lock<std::mutex> lk(mu_);
        cv_.wait_for(lk, std::chrono::milliseconds(20), [this] { return stop_ || !q_.empty(); });
        batch.swap(q_);
      }
      if (udp_) {
        const int a = udp_->poll();   // learn SITL's address; read the armed flag
        if (a >= 0) adapter_->armed(a == 1);
      }
      for (const Msg& m : batch) feed(m);
    }
  }

  void feed(const Msg& m) {
    cur_wall_ = m.wall;
    switch (m.kind) {
      case 0: adapter_->imu(m.t, Vector3(m.v[0], m.v[1], m.v[2]), Vector3(m.v[3], m.v[4], m.v[5])); break;
      case 1: adapter_->att(m.t, Vector3(m.v[0], m.v[1], m.v[2])); break;
      case 2: adapter_->range(m.t, m.v[0]); break;
      case 3: adapter_->flow(m.t, m.v[0], m.v[1], m.v[2] != 0.0, m.v[3]); break;
      case 4: adapter_->heading(m.t, m.v[0], m.v[1], m.v[2]); break;
      case 5: adapter_->tag(m.t, m.v[0], m.v[1], m.v[2]); break;
      case 7: adapter_->time_ref(m.t, m.v[0]); break;
      default: break;
    }
  }

  void write_stats() {
    if (stats_path_.empty()) return;
    if (FILE* f = std::fopen((stats_path_ + ".f64").c_str(), "wb")) {
      std::fwrite(stats_.data(), sizeof(double), stats_.size(), f);
      std::fclose(f);
    }
    if (FILE* f = std::fopen((stats_path_ + ".json").c_str(), "w")) {
      std::fprintf(f, "{\"impl\": \"cpp\", \"config\": \"%s\", \"columns\": [\"t_k\", \"valid\", \"sent\", \"t_us\", "
                   "\"step_ns\", \"lag_s\", \"x\", \"y\", \"z\", \"yaw\"], \"n_keyframes\": %zu, \"n_sent\": %zu, "
                   "\"n_unsettled\": %zu, \"n_unsent_no_peer\": %zu, \"n_reinits\": %zu, \"gap_invalid\": %s, \"t_armed_header\": %.6f, "
                   "\"max_lateness_s\": %.6f, \"n_out_of_order\": %zu, \"n_heading_rejected\": %zu, \"n_imu_unpaired\": %zu, "
                   "\"tref_settled\": %s, \"tref_seed_th\": %s, \"tref_seed_offset_s\": %s, \"n_held\": %zu, "
                   "\"tref_max_track_err_s\": %.6f, \"n_dup_stamp\": %zu}\n",
                   cfg_desc_.c_str(), stats_.size() / 10, adapter_->n_sent, adapter_->n_unsettled, n_unsent_,
                   adapter_->n_reinits, adapter_->gap_invalid ? "true" : "false", adapter_->t_armed_header, adapter_->max_lateness(),
                   adapter_->n_out_of_order(), adapter_->n_hdg_rejected, adapter_->n_imu_unpaired,
                   adapter_->tref_settled ? "true" : "false", jnum(adapter_->tref_seed_th).c_str(),
                   jnum(adapter_->tref_seed_offset).c_str(), adapter_->n_held, adapter_->tref_max_track_err,
                   adapter_->n_dup_stamp);
      std::fclose(f);
    }
  }

  void output(const fgo_cpp::LiveOutput& o) {
    geometry_msgs::msg::PoseStamped p;
    p.header.frame_id = "map";
    p.header.stamp.sec = static_cast<int32_t>(std::floor(o.t_k));
    p.header.stamp.nanosec = static_cast<uint32_t>(std::llround((o.t_k - std::floor(o.t_k)) * 1e9) % 1000000000LL);
    p.pose.position.x = o.row[10]; p.pose.position.y = o.row[11]; p.pose.position.z = o.row[12];
    gtsam::Matrix3 R;
    for (int a = 0; a < 3; ++a)
      for (int b = 0; b < 3; ++b) R(a, b) = o.row[13 + 3 * a + b];
    const auto qq = gtsam::Rot3(R).toQuaternion();
    p.pose.orientation.w = qq.w(); p.pose.orientation.x = qq.x(); p.pose.orientation.y = qq.y(); p.pose.orientation.z = qq.z();
    std_msgs::msg::Bool b;
    b.data = o.valid;
    if (rclcpp::ok()) {   // after SIGINT the context is shut down: the final drain only sends MAVLink and logs stats
      try {
        pub_->publish(p);
        pub_valid_->publish(b);
      } catch (const std::exception&) {
      }
    }
    if (udp_ && o.sent && !udp_->send(o.frame)) ++n_unsent_;
    const double lag = std::chrono::duration<double>(std::chrono::steady_clock::now() - cur_wall_).count();
    const double yaw = std::atan2(o.row[16], o.row[13]);
    const double st_row[10] = {o.t_k, o.valid ? 1.0 : 0.0, o.sent ? 1.0 : 0.0, double(o.t_us), double(o.step_ns), lag,
                               o.row[10], o.row[11], o.row[12], yaw};
    stats_.insert(stats_.end(), st_row, st_row + 10);
  }

  std::unique_ptr<fgo_cpp::LiveAdapter> adapter_;
  std::unique_ptr<fgo_cpp::mav::UdpEndpoint> udp_;
  rclcpp::Publisher<geometry_msgs::msg::PoseStamped>::SharedPtr pub_;
  rclcpp::Publisher<std_msgs::msg::Bool>::SharedPtr pub_valid_;
  std::vector<rclcpp::SubscriptionBase::SharedPtr> subs_;
  std::mutex mu_;
  std::condition_variable cv_;
  std::deque<Msg> q_;
  std::thread worker_;
  std::atomic<bool> stop_{false};
  size_t n_unsent_ = 0;
  std::string stats_path_, cfg_desc_;
  std::vector<double> stats_;   // 10 per keyframe (write_stats columns)
  std::chrono::steady_clock::time_point cur_wall_;
};

int main(int argc, char** argv) {
  rclcpp::init(argc, argv);
  auto n = std::make_shared<FgoCppNode>();
  rclcpp::spin(n);
  n.reset();
  rclcpp::shutdown();
  return 0;
}
