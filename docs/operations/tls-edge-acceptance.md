# FGA HTTPS-edge TLS deployment acceptance

Last updated: 2026-08-28

Status: Accepted normative operations contract under ADR 0036; executable
provider selection and acceptance remain pending

## Scope and owner decision

This gate protects the private, single-owner deployment selected by ADR 0004.
It deliberately requires four different kinds of evidence without turning a
small deployment into a standing six-to-eight-scanner program:

1. the actual supported Lightroom Classic host path through documented
   `LrHttp`;
2. one pinned, reproducible local scanner: `testssl.sh`;
3. one independent hosted scanner: Qualys SSL Labs; and
4. certificate issuance, rollover, renewal, and deployment-restore evidence.

Terry accepted this right-sized set on 2026-08-25. Additional scanners are
diagnostic tools, not votes and not routine private-MVP gates. A transport
incident, a material edge change, or public/multi-user expansion requires a
separate risk review and one or more additional diagnostics selected for the
actual risk. It does not resurrect a permanent vendor matrix by default.

## Provider-neutral edge policy

No HTTPS-edge provider is selected. The eventual provider must expose a TLS
1.3-only policy, managed certificate lifecycle, effective routing/certificate
configuration, and an isolated acceptance host. The Google Cloud candidate maps
those requirements to a global external Application Load Balancer, Google-
managed certificate, `RESTRICTED` SSL policy, and
`preview.flickrgroupaddr.com`; that mapping does not select the provider. The
hosted implementation must export its effective forwarding, routing,
certificate attachment, and TLS policy. Infrastructure-as-code intent alone is
not evidence of the public edge.

The private deployment has no historical-client requirement. Keep TLS 1.3 as
the minimum and accept only the provider's current strong TLS 1.3 suites. Do not
add compatibility speculatively. If the real supported Lightroom Classic host
cannot connect, stop launch and record the failed probe, proposed minimum
relaxation, security consequence, and rollback. Changing the minimum requires
Terry's explicit decision and an accepted ADR amendment before implementation.

Adobe's current `LrHttp` documentation provides no TLS-version selector,
minimum-version promise, or negotiated-version query. A successful request
through a TLS-1.3-only preview edge is therefore the compatibility proof. The
probe may record a protocol or cipher reported by an independently observed
edge, but it must not claim that the FGA LrC plug-in or Lightroom Classic host
reported either value.

## Required client probe

Run the FGA Diligence plug-in in the latest production Lightroom Classic
release offered through Adobe Creative Cloud on the latest production/stable
Windows release adopted by Terry. The plug-in must use a documented `LrHttp`
call to the exact preview hostname and complete a safe authenticated build-bound
FGA API request. A generic browser, `curl`, a Lua socket library, or a mocked
request cannot substitute for the Lightroom Classic host networking stack.

Retain only sanitized evidence:

- Lightroom Classic, Windows, and FGA Diligence versions;
- UTC start/finish times and target hostname;
- expected and observed HTTP status/category;
- immutable FGA web image digest and reported build identifier; and
- pass/fail plus a sanitized error category.

Never retain credentials, cookies, OAuth headers, catalog identifiers, private
photo data, or unverified filenames/paths. Terry's current administrative
browsers must also complete the control-plane and Flickr OAuth callback smoke
flows for the same preview revision. Those are required application checks,
not extra TLS scanners.

## Required local assessment

Use the upstream [`testssl.sh` v3.2.4
release](https://github.com/testssl/testssl.sh/releases/tag/v3.2.4), verified as
the latest stable release on 2026-08-26. Pin that tag and the downloaded
artifact's SHA2-256 in the hosted implementation's operational lock data; never
follow a moving branch or `latest` container tag. A pin change receives an
ordinary dependency, maintenance, license, and result-delta review.

`testssl.sh` is a mature GPL-2.0 external operational tool. Invoke it
unmodified; do not copy, vendor, or reimplement its scanner in the FGA
repository. The orchestration wrapper, when needed, is Python. The third-party
scanner itself remains its native shell implementation because replacing it
would discard a maintained specialist implementation and its test corpus.

Run a complete non-interactive scan against the exact SNI hostname. The pinned
[`testssl.sh` output
contract](https://github.com/testssl/testssl.sh/blob/v3.2.4/doc/testssl.1.md)
supports `--warnings batch` and `--jsonfile-pretty`; retain the structured JSON
without filtering lower-severity results. Record the resolved addresses. When
both A and AAAA records are advertised, exercise each address family while
preserving the hostname/SNI. The provider export establishes that one policy is
attached globally; scanning every edge region is not a separate private-MVP
requirement. Any observed endpoint divergence still blocks acceptance.

The local assessment passes only when:

- TLS 1.2 and older protocols are refused and TLS 1.3 succeeds;
- the effective suites, groups, signatures, and forward-secrecy behavior match
  the selected strong policy;
- the certificate hostname, chain, validity, SNI behavior, and advertised
  address families are correct;
- no `WARN` indicates an incomplete or unreliable scan; and
- no unresolved vulnerability or material `LOW`, `MEDIUM`, `HIGH`, or
  `CRITICAL` finding remains.

A surprising result is investigated and dispositioned. It is never outvoted by
the hosted assessment.

## Required independent hosted assessment

Run a fresh [Qualys SSL Labs Server
Test](https://www.ssllabs.com/ssltest/) against the exact public preview
hostname after DNS and the selected managed certificate are active. Require every
reported endpoint to finish successfully with `A+`, no warning, the expected
certificate/hostname, and TLS 1.3 as the only enabled protocol. Inspect the
details; the grade alone is not sufficient.

Retain the completed report or result link, endpoint inventory, engine and
criteria versions when exposed, test time, and material details. Automation is
optional. If the hosted implementation uses the [SSL Labs assessment
API](https://github.com/ssllabs/ssllabs-scan/blob/master/ssllabs-api-docs-v3.md),
it must first review and comply with the current terms, availability response,
cool-off, concurrency, and polling guidance; a custom API client is not an FGA
requirement.

SSL Labs unavailability blocks initial launch and planned edge-change
acceptance because the independent result is required. It does not justify
loosening the edge. During an emergency restore, the incident runbook may
restore only the last accepted configuration and immutable artifact after the
real-client and local checks pass, but the gate remains visibly incomplete and
the hosted assessment runs as soon as the service returns.

## Certificate and deployment lifecycle

### Initial issuance

Before first preview or production traffic, retain the certificate resource and
attachment identity, managed status `ACTIVE`, covered hostname, observed chain,
serial/fingerprint, validity interval, DNS evidence, expiry alert, and effective
provider export. Both required scanners and the real-client probe must observe
the same accepted certificate generation.

### Rollover drill

Before initial production launch, prove rollover on preview without replacing
production state:

1. create a replacement managed certificate through reviewed infrastructure code;
2. wait for it to become active before attaching it alongside the accepted
   certificate;
3. observe the replacement through repeated sanitized HTTPS probes without a
   client-visible outage;
4. rerun the Lightroom Classic host probe and both required assessments against
   the resulting generation; and
5. detach the old preview certificate only after the replacement passes, then
   retain the before/after identities and timestamps.

No private key is exported from the managed service. A failed activation,
attachment, probe, or scan stops the drill and leaves the old accepted
certificate attached.

### Managed renewal

Managed renewal cannot honestly be forced at initial acceptance. Before
launch, prove the managed-certificate configuration, provider health/expiry
monitoring, alert delivery, and documented response path. At the first natural
renewal—and every renewal that produces an alert or anomaly—record the new
certificate identity and validity interval and rerun the Lightroom Classic host
probe plus the two required assessments. Until that observation exists, label
automatic renewal `configured; not yet observed`, never `passed`. A renewal
that does not converge with enough validity remaining for the documented
response window blocks continued operation before certificate expiry.

### Deployment restore drill

Before initial production launch and after changing the edge's state/bootstrap
method, recreate the preview HTTPS edge in its isolated project from the
reviewed repository infrastructure code, documented state/bootstrap material, and
immutable web image. Do not use production as the drill target. Prove the
restored forwarding rule, target proxy, URL map, SSL policy, certificate,
hostname, routes, and build identity, then rerun the real-client probe and both
required assessments. A hand-edited console reconstruction does not pass.

## HTTP adjuncts

Plaintext requests must never reach an FGA API handler. Port 80, when exposed,
redirects immediately to the canonical HTTPS origin. Enable HSTS only after
HTTPS and certificate lifecycle behavior are stable, with at least a one-year
`max-age`. Add `includeSubDomains` or preload only after separately inventorying
every subdomain and accepting the harder rollback.

MDN HTTP Observatory and SecurityHeaders.com remain useful browser-facing HTTP
header checks. Their grades are not TLS grades and they are not substitutes for
either required TLS assessment.

## Evidence manifest and decision rule

Bind one acceptance record to all of the following:

- UTC run window, target hostname, resolved address families, and trigger;
- immutable FGA web image digest and reported build identifier;
- infrastructure source revision, reviewed plan SHA2-256, apply identifier, and
  effective provider-export SHA2-256;
- forwarding rule, target proxy, URL map, SSL policy, and certificate resource
  identities;
- sanitized Lightroom Classic host and administrative-browser results;
- pinned `testssl.sh` version/artifact SHA2-256, exact command, exit status, raw
  structured JSON, and output SHA2-256;
- SSL Labs report, endpoint inventory, grade/details, engine/criteria versions
  when available, and retained-report SHA2-256; and
- applicable issuance, rollover, renewal, restore, exception, and finding
  dispositions.

The manifest and retained artifacts must contain no secret or private
application data. All required rows pass for the same effective edge and web
revision. A disagreement, incomplete scan, unexplained endpoint difference, or
unbound artifact fails the gate. No majority rule applies.

## Retesting and expansion triggers

Run the complete core gate:

- before initial production use;
- after a DNS, certificate, SSL policy, load balancer, proxy, HSTS, or other
  material public-edge change;
- after each required Lightroom Classic major upgrade, and after a point
  release when its smoke probe changes or fails;
- for certificate rollover, anomalous renewal, and deployment restore; and
- quarterly while the private service is deployed.

After a security incident, material edge change, or proposed public/multi-user
expansion, perform a documented risk review and add diagnostics suited to the
risk—for example targeted OpenSSL, SSLyze, Nmap, Hardenize, or another maintained
independent assessment. Record why each additional tool is used, its pin/terms
and evidence, and the finding disposition. These diagnostics supplement the
core decision; they do not become a permanent private-MVP matrix without a new
accepted decision.
