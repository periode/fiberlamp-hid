var osc = require('node-osc');
var path = require('path');
var bodyparser = require('body-parser')
var express = require('express');
var app = express();

app.use(bodyparser.urlencoded({ extended: false }));
app.use(bodyparser.json());

var http_port = 2046;
app.set('port', http_port);

app.listen(app.get('port'), function(){
  console.log('listening on port',app.get('port'));
});

app.get('/', sendOSCGreeting);
app.post('/change', sendChange);
app.post('/color', sendColor);
app.post('/heartbeat', sendHeartbeat);

//osc
var ip = '127.0.0.1';
var osc_port = 7000;
var client = new osc.Client(ip, osc_port);

function sendOSCGreeting(req, res){
  res.sendFile(path.join(__dirname, './public', 'index.html'));

  /*-----
  
  client.send('/', 'hello', function(err){
    if(err)
      console.log(err);
    console.log('sent');
    client.kill();
  });

  --- or
  var msg = new osc.Message('/');
  msg.append('hey');
  client.send(msg);

  -----*/
}

function sendChange(req, res){
  var data = [parseInt(req.body.r), parseInt(req.body.g), parseInt(req.body.b), parseInt(req.body.t)];

  client.send('/change', data, function(err){
    if(err)
      console.log(err);
    console.log('change sent: '+data);
  });

  res.send('change: '+data+' sent successfully');
}

function sendColor(req, res){
  var data = [parseInt(req.body.r), parseInt(req.body.g), parseInt(req.body.b)];
  console.log('sending data',data);
  client.send('/color', data, function(err){
    if(err)
      console.log(err);
    console.log('color sent: '+data);
  });

  res.send('color: '+data+' sent successfully');
}

function sendHeartbeat(req, res){
  var data = 'heartbeat';

  client.send('/transition', data, function(err){
    if(err)
      console.log(err);
    console.log('transition sent: '+data);
  });

  res.send('transition: '+data+' sent successfully');
}
