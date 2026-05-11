import re
import sys
import subprocess
import socket
import time
import http.client
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

    def run_tcp(self, host: str, port: int, count: int = 4, timeout_sec: int = 2) -> dict:
        """
        Emulate ping at the application layer by creating socket connections.
        Measures individual packet transmission and calculates min/max/avg latency.
        """
        latencies = []
        error_msg = "Unknown error"
        
        for i in range(count):
            start = time.perf_counter()
            try:
                # Intenta abrir el socket y cerrarlo inmediatamente
                with socket.create_connection((host, port), timeout=timeout_sec):
                    latency_ms = (time.perf_counter() - start) * 1000
                    latencies.append(latency_ms)
            except socket.timeout:
                error_msg = "Connection timeout (FILTERED/TIMEOUT)"
            except ConnectionRefusedError:
                # The port is closed, but host is UP! However, we treat connection failure as packet loss.
                error_msg = "Connection refused (CLOSED)"
            except Exception as e:
                error_msg = str(e)

        received = len(latencies)
        lost = count - received
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
                "error": error_msg
            }

    def run_dns(self, host: str, count: int = 4, timeout_sec: int = 2) -> dict:
        """
        Emulate ping at the name resolution layer using getaddrinfo.
        Measures individual resolve requests and calculates min/max/avg latency.
        """
        latencies = []
        error_msg = "Unknown error"

        for i in range(count):
            start = time.perf_counter()
            try:
                socket.getaddrinfo(host, None)
                latency_ms = (time.perf_counter() - start) * 1000
                latencies.append(latency_ms)
            except socket.gaierror:
                error_msg = "DNS_RESOLUTION_FAILED"
            except Exception as e:
                error_msg = str(e)

        received = len(latencies)
        lost = count - received
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
                "error": error_msg
            }

    def run_http(self, host: str, port: int, count: int = 4, timeout_sec: int = 2) -> dict:
        """
        Emulate ping at HTTP Layer 7 by making HEAD requests.
        Measures individual requests and calculates min/max/avg latency.
        """
        latencies = []
        error_msg = "Unknown error"

        for i in range(count):
            start = time.perf_counter()
            conn = None
            try:
                conn = http.client.HTTPConnection(host, port, timeout=timeout_sec)
                conn.request("HEAD", "/")
                # If we get any HTTP response (e.g., 200, 403, 404), the server is up!
                response = conn.getresponse()
                latency_ms = (time.perf_counter() - start) * 1000
                latencies.append(latency_ms)
                error_msg = f"HTTP {response.status} {response.reason}"
            except Exception as e:
                error_msg = f"SERVICE_UNREACHABLE: {e}"
            finally:
                if conn:
                    conn.close()

        received = len(latencies)
        lost = count - received
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
                "error": error_msg
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
            methods = endpoint.get("test_methods") or ["ICMP"]
            port = endpoint.get("port") or 80
            count = endpoint.get("packets") or 4
            timeout_sec = endpoint.get("timeout") or 2

            origin_ip = get_origin_ip(host) or "unknown"
            
            for method_raw in methods:
                method = method_raw.lower()
                
                # Execute probe based on method
                self.logger.info(
                    f"Testing target '{host}' via {method.upper()} (origin: '{origin_ip}', alias: '{alias or 'None'}') with {count} tries..."
                )
                
                if method == "icmp":
                    res = self.run_ping(host, count=count, timeout_sec=timeout_sec)
                elif method == "tcp":
                    res = self.run_tcp(host, port=port, count=count, timeout_sec=timeout_sec)
                elif method == "dns":
                    res = self.run_dns(host, count=count, timeout_sec=timeout_sec)
                elif method == "http":
                    res = self.run_http(host, port=port, count=count, timeout_sec=timeout_sec)
                else:
                    self.logger.warning(f"Unsupported connection method '{method}', skipping method.")
                    continue

                # Build dimensions for metric reporting (include 'method' so they don't collide!)
                dimensions = {
                    "origin": origin_ip,
                    "destination": host,
                    "method": method
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
                        f"{method.upper()} successful for {host}: Sent={res['sent']}, Received={res['received']}, "
                        f"Latency (Min/Avg/Max)={res['min']:.1f}/{res['avg']:.1f}/{res['max']:.1f} ms"
                    )
                    self.report_metric("custom.extrg.ping.latency.min", res["min"], dimensions=dimensions)
                    self.report_metric("custom.extrg.ping.latency.max", res["max"], dimensions=dimensions)
                    self.report_metric("custom.extrg.ping.latency.avg", res["avg"], dimensions=dimensions)
                else:
                    self.logger.warning(f"{method.upper()} failed for {host}: {res['error']}")

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


