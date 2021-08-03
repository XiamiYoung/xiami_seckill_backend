from data.out.base_res_body import BaseResBody

class ErrorData(BaseResBody):
    def __init__(self, httpCode):
        self.httpCode = httpCode
        super.__init__()