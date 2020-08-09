# Home Assistant Custom Add-on: Route 53 Dynamic DNS

Route 53 allows for hosting domains and the management of DNS records.
When hosting a server a DNS record must point to your public IP address
in order for your server to be accessible via domain name.
Some ISP's assign you a dynamic public IP address which changes after some time.
This makes your server unreachable by the domain name.
This add-on automatically checks if your Route 53 DNS record is up to date by
updating the public IP Address to your currently assigned IP address to prevent
such outages.

This add-on is very similar to the [AWS Route53 integration](https://www.home-assistant.io/integrations/route53/)
in Home-Assistant core. There are a few differences. The dependencies of this add-on are all AWS maintained.
The add-on uses the AWS SDK [boto3](https://github.com/boto/boto3) package and checks your public IP address
using the [AWS checkip endpoint](https://checkip.amazonaws.com).
The add-on acts as a separate service from Home-Assistant and is not dependent
on Home-Assistant Core.

## Installation

The installation of this add-on is pretty straightforward and not different in
comparison to installing any other Home Assistant add-on.

There is further configuration to be completed on AWS.

A pre-requisite is having a current A record configured for your domain in
a Route 53 hosted zone.

It is recommended that your create a user specifically for this add-on.
You will need to grant the user permissions to Route 53 in IAM policies.

An example of such permissions:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "route53:GetHostedZone",
        "route53:ListHostedZonesByName",
        "route53:ChangeResourceRecordSets",
      ],
      "Resource": [
        "*"
      ]
    }
  ]
}
```

**Note**: _This is just an example, don't copy and paste it! Create your own!_


## Configuration

**Note**: _Remember to restart the add-on when the configuration is changed._

Example add-on configuration:

```yaml
aws_access_key_id: ABC123ABC123
aws_secret_access_key: ABC123ABC123
zone_id: ABC123ABC123
domain_urls:
 - example.com
 - example.example.com
interval: 180
log_level: info
```

**Note**: _This is just an example, don't copy and paste it! Create your own!_

### Option: `aws_access_key_id`

The programatic access key id for your AWS account. Available in the IAM service.

### Option: `aws_secret_access_key`

The programatic secret access key for your AWS account. Available in the IAM service.

### Option: `zone_id`

The zone id of your hosted zone. Avalible in the Route 53 service.

### Option: `domain_urls`

The domain urls to update. Available in the Route 53 Service.

### Option: `interval`

The interval in seconds the add-on will check your public IP address against your DNS records.

### Option: `log_level`

The `log_level` option controls the level of log output by the addon and can
be changed to be more or less verbose, which might be useful when you are
dealing with an unknown issue. Possible values are:

- `trace`: Show every detail, like all called internal functions.
- `debug`: Shows detailed debug information.
- `info`: Normal (usually) interesting events.
- `warning`: Exceptional occurrences that are not errors.
- `error`:  Runtime errors that do not require immediate action.
- `fatal`: Something went terribly wrong. Add-on becomes unusable.

Please note that each level automatically includes log messages from a
more severe level, e.g., `debug` also shows `info` messages. By default,
the `log_level` is set to `info`, which is the recommended setting unless
you are troubleshooting.
