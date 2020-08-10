# Home Assistant Custom Add-on: LAN Bandwith Tester

This add-on installs and runs a simple iperf3 server on
your Docker host network with port 5201. This add-on tests the speed of
your connection between your HA instance and another device.

## Installation

The installation of this add-on is pretty straightforward and not different in
comparison to installing any other Home Assistant add-on.

For client devices **iperf3** must be installed. Installation varies by
OS.

## Configuration

**Note**: _There is no configuration for this add-on._

## Usage

On your client device run iperf3 in terminal.

Test TCP speed:

```bash
iperf3 -c <HA IP address>
```

Test UDP speed with the max bitrate available:

**Warning**: _This may congest and crash your network._

```bash
iperf3 -c <HA IP address> -u -b 0
```

There are numerous variations to running iperf3. See the [iperf3 docs](https://iperf.fr/iperf-doc.php) for more info.
