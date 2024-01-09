var PSign = new ParamsSign({appId:"input_app_id"})
PSign.sign(input_body).then(signedParams => {console.log("h5st:" + signedParams.h5st)});