
/**
 * Module dependencies.
 */

var express = require('express');
var app = express(),
    server = require('http').createServer(app),
    io = require('socket.io').listen(server),
    path = require('path'),
    routes = require('./routes'),
    user = require('./routes/user');


// all environments
app.set('port', process.env.PORT || 3000);
app.set('views', __dirname + '/views');
app.set('view engine', 'ejs');
app.use(express.favicon());
app.use(express.logger('dev'));
app.use(express.bodyParser());
app.use(express.methodOverride());
app.use(app.router);
app.use(express.static(path.join(__dirname, 'public')));

// development only
if ('development' == app.get('env')) {
  app.use(express.errorHandler());
}

app.get('/', routes.index);
app.get('/users', user.list);

server.listen(app.get('port'), function(){
  console.log('Picture Crop System listening on port ' + app.get('port'));
});

io.sockets.on('connection', function(socket) {
    socket.emit('data', {hello: 'hello'});
    socket.on('new request', function(data) {
        console.log('new request', data);
        socket.emit('data', {hello: 'world'});
    });
});
