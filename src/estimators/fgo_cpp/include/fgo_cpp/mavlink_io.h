// Minimal MAVLink 2 I/O for the live FGO adapter, with no MAVLink library dependency:
//  - encode ODOMETRY (#331, CRC_EXTRA 91) exactly as pymavlink 2.4.49 does in fgo_node.py
//    (v2 framing, trailing-zero payload truncation, X.25 CRC, sysid 255 / compid 197, running sequence);
//  - parse incoming v1/v2 frames for HEARTBEAT (#0, CRC_EXTRA 50) to read the autopilot's armed flag;
//  - a UDP endpoint with pymavlink "udp:host:port" semantics: bind and LISTEN on host:port, reply to the
//    last address a datagram came from (SITL SERIAL3 udpclient heartbeats), send nothing before that.
// Verified byte-for-byte against pymavlink (tools/check_mavlink_encoding.py).
#pragma once

#include <array>
#include <cstdint>
#include <cstring>
#include <string>
#include <vector>

#include <arpa/inet.h>
#include <fcntl.h>
#include <netinet/in.h>
#include <sys/socket.h>
#include <unistd.h>

namespace fgo_cpp {
namespace mav {

constexpr uint8_t FRAME_LOCAL_NED = 1, FRAME_BODY_FRD = 12, ESTIMATOR_NAIVE = 1;

inline void crc_acc(uint8_t b, uint16_t& crc) {
  uint8_t tmp = b ^ static_cast<uint8_t>(crc & 0xff);
  tmp ^= static_cast<uint8_t>(tmp << 4);
  crc = static_cast<uint16_t>((crc >> 8) ^ (tmp << 8) ^ (tmp << 3) ^ (tmp >> 4));
}

struct Odometry {
  uint64_t time_usec = 0;
  float x = 0, y = 0, z = 0;
  float q[4] = {1, 0, 0, 0};
  float vx = 0, vy = 0, vz = 0, rollspeed = 0, pitchspeed = 0, yawspeed = 0;
  float pose_covariance[21], velocity_covariance[21];
  uint8_t frame_id = FRAME_LOCAL_NED, child_frame_id = FRAME_BODY_FRD, reset_counter = 0, estimator_type = ESTIMATOR_NAIVE;
  int8_t quality = 0;
};

template <class T>
inline void put(std::vector<uint8_t>& b, T v) {
  uint8_t tmp[sizeof(T)];
  std::memcpy(tmp, &v, sizeof(T));   // little-endian host (x86-64, aarch64)
  b.insert(b.end(), tmp, tmp + sizeof(T));
}

// One MAVLink 2 frame (unsigned).
inline std::vector<uint8_t> frame_v2(uint32_t msgid, uint8_t crc_extra, std::vector<uint8_t> payload, uint8_t seq,
                                     uint8_t sysid, uint8_t compid) {
  while (payload.size() > 1 && payload.back() == 0) payload.pop_back();   // MAVLink 2 trailing-zero truncation
  std::vector<uint8_t> f = {0xFD, static_cast<uint8_t>(payload.size()), 0, 0, seq, sysid, compid,
                            static_cast<uint8_t>(msgid & 0xff), static_cast<uint8_t>((msgid >> 8) & 0xff),
                            static_cast<uint8_t>((msgid >> 16) & 0xff)};
  f.insert(f.end(), payload.begin(), payload.end());
  uint16_t crc = 0xffff;
  for (size_t i = 1; i < f.size(); ++i) crc_acc(f[i], crc);
  crc_acc(crc_extra, crc);
  f.push_back(static_cast<uint8_t>(crc & 0xff));
  f.push_back(static_cast<uint8_t>(crc >> 8));
  return f;
}

inline std::vector<uint8_t> encode_odometry(const Odometry& m, uint8_t seq, uint8_t sysid = 255, uint8_t compid = 197) {
  std::vector<uint8_t> p;   // wire order (pymavlink format "<Qfff4fffffff21f21fBBBBb")
  put(p, m.time_usec);
  put(p, m.x); put(p, m.y); put(p, m.z);
  for (float v : m.q) put(p, v);
  put(p, m.vx); put(p, m.vy); put(p, m.vz);
  put(p, m.rollspeed); put(p, m.pitchspeed); put(p, m.yawspeed);
  for (float v : m.pose_covariance) put(p, v);
  for (float v : m.velocity_covariance) put(p, v);
  put(p, m.frame_id); put(p, m.child_frame_id); put(p, m.reset_counter); put(p, m.estimator_type); put(p, m.quality);
  return frame_v2(331, 91, p, seq, sysid, compid);
}

// Scan a datagram for HEARTBEAT frames from an autopilot (any sysid, compid 1); returns -1 if none, else 0/1 armed.
inline int heartbeat_armed(const uint8_t* d, size_t n) {
  int armed = -1;
  size_t i = 0;
  while (i < n) {
    if (d[i] == 0xFD && i + 12 <= n) {
      const size_t len = d[i + 1], hdr = 10;
      const bool signed_ = d[i + 2] & 1;
      const size_t tot = hdr + len + 2 + (signed_ ? 13 : 0);
      if (i + tot > n) break;
      const uint32_t msgid = d[i + 7] | (d[i + 8] << 8) | (d[i + 9] << 16);
      if (msgid == 0 && d[i + 6] == 1) {
        uint16_t crc = 0xffff;
        for (size_t k = 1; k < hdr + len; ++k) crc_acc(d[i + k], crc);
        crc_acc(50, crc);
        if ((crc & 0xff) == d[i + hdr + len] && (crc >> 8) == d[i + hdr + len + 1]) {
          uint8_t pl[9] = {0};   // truncated payload: missing bytes are zero
          std::memcpy(pl, d + i + hdr, len < 9 ? len : 9);
          armed = (pl[6] & 0x80) ? 1 : 0;   // base_mode & MAV_MODE_FLAG_SAFETY_ARMED
        }
      }
      i += tot;
    } else if (d[i] == 0xFE && i + 8 <= n) {
      const size_t len = d[i + 1], tot = 6 + len + 2;
      if (i + tot > n) break;
      if (d[i + 5] == 0 && d[i + 4] == 1) {
        uint16_t crc = 0xffff;
        for (size_t k = 1; k < 6 + len; ++k) crc_acc(d[i + k], crc);
        crc_acc(50, crc);
        if ((crc & 0xff) == d[i + 6 + len] && (crc >> 8) == d[i + 6 + len + 1] && len >= 7)
          armed = (d[i + 6 + 6] & 0x80) ? 1 : 0;
      }
      i += tot;
    } else {
      ++i;
    }
  }
  return armed;
}

// pymavlink "udp:host:port" (listen) semantics.
class UdpEndpoint {
 public:
  explicit UdpEndpoint(const std::string& spec) {   // "udp:127.0.0.1:14558" or "127.0.0.1:14558"
    std::string s = spec.rfind("udp:", 0) == 0 ? spec.substr(4) : spec;
    const size_t c = s.rfind(':');
    const std::string host = s.substr(0, c);
    const int port = std::stoi(s.substr(c + 1));
    fd_ = ::socket(AF_INET, SOCK_DGRAM, 0);
    sockaddr_in a{};
    a.sin_family = AF_INET;
    a.sin_port = htons(static_cast<uint16_t>(port));
    ::inet_pton(AF_INET, host.c_str(), &a.sin_addr);
    int one = 1;
    ::setsockopt(fd_, SOL_SOCKET, SO_REUSEADDR, &one, sizeof(one));
    ok_ = ::bind(fd_, reinterpret_cast<sockaddr*>(&a), sizeof(a)) == 0;
    ::fcntl(fd_, F_SETFL, ::fcntl(fd_, F_GETFL) | O_NONBLOCK);
  }
  ~UdpEndpoint() { if (fd_ >= 0) ::close(fd_); }
  bool ok() const { return ok_; }
  bool have_peer() const { return have_peer_; }
  // Drain everything received; remember the sender; returns the latest armed flag seen (-1 none).
  int poll() {
    int armed = -1;
    uint8_t buf[2048];
    while (true) {
      sockaddr_in from{};
      socklen_t fl = sizeof(from);
      const ssize_t n = ::recvfrom(fd_, buf, sizeof(buf), 0, reinterpret_cast<sockaddr*>(&from), &fl);
      if (n <= 0) break;
      peer_ = from; have_peer_ = true;
      const int a = heartbeat_armed(buf, static_cast<size_t>(n));
      if (a >= 0) armed = a;
    }
    return armed;
  }
  bool send(const std::vector<uint8_t>& f) {
    if (!have_peer_) return false;
    return ::sendto(fd_, f.data(), f.size(), 0, reinterpret_cast<const sockaddr*>(&peer_), sizeof(peer_)) ==
           static_cast<ssize_t>(f.size());
  }

 private:
  int fd_ = -1;
  bool ok_ = false, have_peer_ = false;
  sockaddr_in peer_{};
};

}  // namespace mav
}  // namespace fgo_cpp
