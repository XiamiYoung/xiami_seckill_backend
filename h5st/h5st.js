var fs = require("fs");
const jsdom = require("jsdom");
const { JSDOM } = jsdom;
var express = require('express');
var capcon = require('capture-console');

var app = express();
app.use(express.json());

var security_js = fs.readFileSync('./js_security_v3.js');
var calculate_js_original = fs.readFileSync('./calculate.js');
var dom = new JSDOM('<body><script>'  + security_js + '</script></body>', {url: "https:/asdf213123eassad.com/", runScripts: "dangerously"});
global.window = dom.window

function get_h5st(){
    var temp_calculate_js = calculate_js_original
    
    var appId = "dummy";
    var functionId = "dummy";
    var time = 1;
    var body = "dummy";

    temp_calculate_js = temp_calculate_js.toString().replace(/input_body/g,body)
    temp_calculate_js = temp_calculate_js.toString().replace(/input_time/g,time)
    temp_calculate_js = temp_calculate_js.toString().replace(/input_app_id/g,appId)
    temp_calculate_js = temp_calculate_js.toString().replace(/input_function_id/g,functionId)

    var output = '';
    capcon.startCapture(process.stdout, function (stdout) {
        output += stdout;
    });
    
    dom.window.eval(temp_calculate_js);
    return output
}

app.post('/h5st', function(request, response){
    var temp_calculate_js = calculate_js_original
    var appId = request.body.appId;
    var functionId = request.body.functionId;
    var time = request.body.time;
    var body = request.body.body;

    temp_calculate_js = temp_calculate_js.toString().replace(/input_body/g,body)
    temp_calculate_js = temp_calculate_js.toString().replace(/input_time/g,time)
    temp_calculate_js = temp_calculate_js.toString().replace(/input_app_id/g,appId)
    temp_calculate_js = temp_calculate_js.toString().replace(/input_function_id/g,functionId)

    var output = '';
    capcon.startCapture(process.stdout, function (stdout) {
        output += stdout;
    });
    
    dom.window.eval(temp_calculate_js);

    setTimeout(function(){ response.send(output) }, 300);

});

app.listen(3000);
console.log('server started')
// warm up
get_h5st()