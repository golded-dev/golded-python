# Security reports

Do not disclose private messages, message bases, operator paths or credentials in
public issues. Use GitHub's private vulnerability reporting for the repository when
enabled; otherwise contact the repository owner through their GitHub profile and
request a private channel before sharing details. No dedicated security email or
response SLA is promised. Ordinary bugs without sensitive details belong in Issues.

golded opens only bases with the golded-ftn-sqlite application ID and schema
version, and writes only when you save a message. Message text is displayed, not
executed. A base and its `-wal` and `-shm` files hold message contents in plain
text; protect them as you would the messages.
