To run test we use locust.io

## Test with UI interface and diagrams
```bash
/usr/local/bin/locust --users 10 --spawn-rate 10 -f orig_api_test.py
```

## Test using cli
```bash
/usr/local/bin/locust --headless --users 10 --spawn-rate 10 -f orig_api_test.py --host https://recoapi-ng-dev.theglobeandmail.com
```
