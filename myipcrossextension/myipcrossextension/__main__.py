import re
import sys
import subprocess
import socket
from dynatrace_extension import Extension, Status, StatusValue


def get_origin_ip(host: str) -> str | None:
    """Resolve the local source IP used to reach the destination host."""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
            sock.connect((host, 1))
            return sock.getsockname()[0]
    except Exception:
        return None


class ExtensionImpl(Extension):
    def run_ping(self, host: str, count: int = 4, timeout_sec: int = 2) -> dict:
        """
        Execute the system ping command across Windows and Linux platforms.
        Parses output in a language-agnostic manner to extract packets and latency.
        """
        is_windows = sys.platform.lower().startswith("win")
        
        if is_windows:
            timeout_ms = timeout_sec * 1000
            cmd = ["ping", "-n", str(count), "-w", str(timeout_ms), host]
        else:
            cmd = ["ping", "-c", str(count), "-W", str(timeout_sec), host]

        self.logger.debug(f"Executing command: {' '.join(cmd)}")

        try:
            # Execute ping command
            # We set a process timeout to avoid hanging the extension if DNS or system hangs
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=False,
                timeout=(count * timeout_sec) + 5
            )
            # Decode using OEM CP for Windows (usually ANSI/cp850/cp1252) or UTF-8 for Linux
            output = result.stdout.decode("ansi" if is_windows else "utf-8", errors="ignore")
        except subprocess.TimeoutExpired:
            self.logger.error(f"Ping process timed out for host {host}")
            return {
                "host": host,
                "sent": count,
                "received": 0,
                "lost": count,
                "loss_percent": 100.0,
                "min": None,
                "max": None,
                "avg": None,
                "status": 0,
                "error": "TimeoutExpired"
            }
        except Exception as e:
            self.logger.error(f"Error executing ping for host {host}: {e}")
            return {
                "host": host,
                "sent": count,
                "received": 0,
                "lost": count,
                "loss_percent": 100.0,
                "min": None,
                "max": None,
                "avg": None,
                "status": 0,
                "error": str(e)
            }

        # Parse output for reply lines with latency values.
        # This is language-independent because we match 'time=' or 'tiempo=' followed by '=' or '<' and decimal values.
        latencies = []
        for line in output.splitlines():
            match = re.search(r"(?:time|tiempo)[=<]([\d\.]+)", line, re.IGNORECASE)
            if match:
                try:
                    latencies.append(float(match.group(1)))
                except ValueError:
                    pass

        received = len(latencies)
        lost = count - received
        if lost < 0:
            lost = 0
        loss_percent = (lost / count) * 100.0 if count > 0 else 100.0

        if received > 0:
            return {
                "host": host,
                "sent": count,
                "received": received,
                "lost": lost,
                "loss_percent": loss_percent,
                "min": min(latencies),
                "max": max(latencies),
                "avg": sum(latencies) / received,
                "status": 1,
                "error": None
            }
        else:
            return {
                "host": host,
                "sent": count,
                "received": 0,
                "lost": count,
                "loss_percent": 100.0,
                "min": None,
                "max": None,
                "avg": None,
                "status": 0,
                "error": "No response"
            }

    def query(self):
        """
        The query method is automatically scheduled to run every minute
        """
        self.logger.info("Query method started for custom:myipcrossextension.")

        # Ensure endpoints configuration is available
        endpoints = self.activation_config.get("endpoints")
        if not endpoints:
            self.logger.warning("No endpoints configured for myipcrossextension.")
            return

        for endpoint in endpoints:
            host = endpoint.get("host")
            if not host:
                self.logger.warning("Configured endpoint lacks a 'host' key, skipping.")
                continue

            alias = endpoint.get("alias") or ""
            count = endpoint.get("packets") or 4
            timeout_sec = endpoint.get("timeout") or 2

            origin_ip = get_origin_ip(host) or "unknown"
            self.logger.info(
                f"Pinging target '{host}' (origin: '{origin_ip}', alias: '{alias or 'None'}') with {count} packets..."
            )
            
            # Execute the ping
            res = self.run_ping(host, count=count, timeout_sec=timeout_sec)

            # Build dimensions for metric reporting
            dimensions = {
                "origin": origin_ip,
                "destination": host
            }
            if alias:
                dimensions["alias"] = alias

            # Report standard metrics
            self.report_metric("custom.extrg.ping.packets.sent", res["sent"], dimensions=dimensions)
            self.report_metric("custom.extrg.ping.packets.received", res["received"], dimensions=dimensions)
            self.report_metric("custom.extrg.ping.packets.lost", res["lost"], dimensions=dimensions)
            self.report_metric("custom.extrg.ping.loss.percent", res["loss_percent"], dimensions=dimensions)
            self.report_metric("custom.extrg.ping.status", res["status"], dimensions=dimensions)

            # Report latency metrics only if we received at least one response
            if res["received"] > 0:
                self.logger.info(
                    f"Ping successful for {host}: Sent={res['sent']}, Received={res['received']}, "
                    f"Latency (Min/Avg/Max)={res['min']:.1f}/{res['avg']:.1f}/{res['max']:.1f} ms"
                )
                self.report_metric("custom.extrg.ping.latency.min", res["min"], dimensions=dimensions)
                self.report_metric("custom.extrg.ping.latency.max", res["max"], dimensions=dimensions)
                self.report_metric("custom.extrg.ping.latency.avg", res["avg"], dimensions=dimensions)
            else:
                self.logger.warning(f"Ping failed for {host}: {res['error']}")

        self.logger.info("Query method ended for custom:myipcrossextension.")

    def fastcheck(self) -> Status:
        """
        Use to check if the extension can run.
        """
        return Status(StatusValue.OK)


def main():
    ExtensionImpl(name="myipcrossextension").run()


if __name__ == "__main__":
    main()

