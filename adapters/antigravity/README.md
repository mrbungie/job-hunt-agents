# Antigravity adapter

Install project-scoped with `python3 bin/install-host.py --host antigravity
--project <project>`. Run `bin/preflight.py` explicitly. In particular, this
package does not treat `PreInvocation` as a session-start event and installs no
repeated preflight hook.
