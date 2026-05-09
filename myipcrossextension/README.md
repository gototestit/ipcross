# custom:myipcrossextension

**Latest version:** 0.0.1
This extension is built using the Dynatrace Extension 2.0 Framework.
This means it will benefit of additional assets that can help you browse through the data.

## Metrics

This extension will collect the following metrics:
* Split by :
  * Ping Packets Sent (`custom.ping.packets.sent`)
    Number of ping packets sent (as Count)
  * Ping Packets Received (`custom.ping.packets.received`)
    Number of successful ping replies received (as Count)
  * Ping Packets Lost (`custom.ping.packets.lost`)
    Number of ping packets lost (as Count)
  * Ping Packet Loss Percent (`custom.ping.loss.percent`)
    Percentage of ping packets lost (as Percent)
  * Ping Status (`custom.ping.status`)
    Ping status (1 = OK, 0 = Failure) (as Count)
  * Ping Latency (Min) (`custom.ping.latency.min`)
    Minimum latency of successful pings (as MilliSecond)
  * Ping Latency (Max) (`custom.ping.latency.max`)
    Maximum latency of successful pings (as MilliSecond)
  * Ping Latency (Avg) (`custom.ping.latency.avg`)
    Average latency of successful pings (as MilliSecond)

# Configuration

## Feature sets

Feature sets can be used to opt in and out of metric data collection.
This extension groups together metrics within the following feature sets:

* default

