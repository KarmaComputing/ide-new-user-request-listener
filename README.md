# ide-new-user-request-listener

Listens for new username requests on https://ide.example.co.uk/

- Calls ../generate-ide-username.sh to generate a username
- http json response to the user instantly with that username
- Appends the new username to a file ../ide-creation-queue for a consumer to
  generate the IDE
- Allows the caller to poll instantly based on the username they get back
  (poll the web address karma-ide-user-<username>.ide.example.co.uk

## Run

There's currently no external dependencies (so no `pip` / `uv` etc etc needed)

```
./run.sh
```

## Test

```
./test.sh
```
