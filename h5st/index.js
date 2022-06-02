var vm = require("vm");
var fs = require("fs");
const jsdom = require("jsdom");
const { JSDOM } = jsdom;

var args = process.argv.slice(2);
console.log(args)

var app_id = args[0]
var function_id = args[1]
var t = args[2]
var body = args[3]

var security_js = fs.readFileSync('./js_security_v3.js');
var calculate_js = fs.readFileSync('./calculate.js');

calculate_js = calculate_js.toString().replace(/input_body/g,body)
calculate_js = calculate_js.toString().replace(/input_time/g,t)
calculate_js = calculate_js.toString().replace(/input_app_id/g,app_id)
calculate_js = calculate_js.toString().replace(/input_function_id/g,function_id)

const dom = new JSDOM('<body><script>'  + security_js + calculate_js + '</script></body>', {url: "https:/asdf213123eassad.com/", runScripts: "dangerously"});
