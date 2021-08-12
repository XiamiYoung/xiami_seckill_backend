ps -ef | grep uvicorn | grep -v grep | awk '{print $2}' | xargs kill
ps -ef | grep python3 | grep -v grep | awk '{print $2}' | xargs kill