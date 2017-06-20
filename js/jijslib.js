/* JavaScript generic functions, constants. Expects jQuery is present */

function simulateKeyEvent(which, event) {
  /* Simulate pressing of keyboard key with code = which
     event is 'keydown', 'keypress', or 'keyup'
     Called from simulateKeyEvents 
  */
  if (!event) {
    event = 'keydown'
  }
  if (typeof(which) == "string") {
    which = which.charCodeAt(0);
  }
  jQuery.event.trigger({ type : event, which : which });
}

function simulateKeyEvents(characterOrCodes, event) {
  /* Simulate pressing keyboard characters specified either as a string
     or array of characters or keycodes */
  var type = typeof(characterOrCodes);
  if (type == "number") {
    simulateKeyEvent(characterOrCodes, event);
  } else if ((type == "string") && (characterOrCodes.length == 1)) {
    simulateKeyEvent(characterOrCodes.charCodeAt(0), event);
  } else if (characterOrCodes.length) {
    for (i = 0; i < characterOrCodes.length; i++) {
      simulateKeyEvent(characterOrCodes[i], event);
    }
  }  
}

// jQuery extensions

jQuery.extend(jQuery.expr[':'], {
  focused: function(element) { 
    return element == document.activeElement; 
  }
});

/*
   http://think-robot.com/2009/06/hitch-object-oriented-event-handlers-with-jquery/
  Usage - instead of 
     .bind('click', obj.method)
  use
     .hitch('click', obj.method, obj)
  
  so that obj.method is called in the context of obj and not the event.target
*/

(function($) {
  $.fn.hitch = function(ev, fn, scope) {
    return this.bind(ev, function() {
      return fn.apply(scope || this, Array.prototype.slice.call(arguments));
    });
  };
})(jQuery);
// /jQuery extensions

/* Extending prototype of standard classes */
// String
String.prototype.format = function() {
  var formatted = this;
  for (arg in arguments) {
    formatted = formatted.replace("{" + arg + "}", arguments[arg]);
  }
  return formatted;
};


// http://snippets.dzone.com/posts/show/701
String.prototype.trim = function() { return this.replace(/^\s+|\s+$/g, ''); };
String.prototype.strip = String.prototype.trim


//trimming space from left side of the string
String.prototype.ltrim = function() {
  return this.replace(/^\s+/,"");
}
 
//trimming space from right side of the string
String.prototype.rtrim = function() {
  return this.replace(/\s+$/,"");
}


//pads left
String.prototype.lpad = function(padString, length) {
  var str = '' + this;
  while (str.length < length)
    str = padString + str;
  return str;
}
 
//pads right
String.prototype.rpad = function(padString, length) {
  var str = '' + this;
  while (str.length < length)
    str = str + padString;
  return str;
}




// /String

// The shift() and unshift() methods.
if(!Array.prototype.shift) { // if this method does not exist..

	Array.prototype.shift = function(){
		firstElement = this[0];
		this.reverse();
		this.length = Math.max(this.length-1,0);
		this.reverse();
		return firstElement;
	}
	
}

if(!Array.prototype.unshift) { // if this method does not exist..
	
	Array.prototype.unshift = function(){
		this.reverse();
		
			for(var i=arguments.length-1;i>=0;i--){
				this[this.length]=arguments[i]
			}
			
		this.reverse();
		return this.length
	}
}
/* /Extending prototype of standard classes */
//http://www.javascriptkit.com/javatutors/oopjs2.shtml

/* Constants */
var VK_BACKSPACE = 8;
var VK_TAB = 9;
var VK_ENTER = 13;
var VK_SHIFT = 16;
var VK_CTRL = 17;
var VK_ALT = 18;
var VK_PAUSE = 19;
var VK_ESCAPE = 27;
var VK_INSERT = 45;
var VK_DELETE = 46; 
var VK_DOT = 190;
var VK_COMMA = 188;

var VK_NUM_0 = 96;
var VK_NUM_9 = 105;
var VK_NUM_PLUS = 107;
var VK_NUM_MINUS = 109;
var VK_NUM_MULTIPLY = 106;
var VK_NUM_DOT = 110;
var VK_NUM_DIVIDE = 111;

var VK_DELETE = 46;
var VK_ESC = 27;
var VK_END = 35;
var VK_HOME = 36;
var VK_LEFT = 37;
var VK_UP = 38;
var VK_RIGHT = 39;
var VK_DOWN = 40;

var VK_F1 = 112;
var VK_F2 = 113;
var VK_F3 = 114;
var VK_F4 = 115;
var VK_F5 = 116;
var VK_F6 = 117;
var VK_F7 = 118;
var VK_F8 = 119;
var VK_F9 = 120;
var VK_F10 = 121;
var VK_F11 = 122;
var VK_F12 = 123;


/* /Constants */

// localStorage 
function getStorageObject(key, default_obj) {
  // http://stackoverflow.com/questions/2010892/storing-objects-in-html5-localstorage
  var res = localStorage.getItem(key) && JSON.parse(localStorage.getItem(key));
  if (!res) {
     res = default_obj;
  }
  return res;
}
function setStorageObject(key, obj) {
  localStorage.setItem(key, JSON.stringify(obj));
}
// /localStorage

/* Date functions */
var daysOfWeek = ["Ne", "Po", "Út", "St", "Čt", "Pá", "So"];

function lzero(d) {
  d = "" + d;
  if (d.length === 1) {
     d = '0' + d;
  }
  return d;
}

function getISODateTimeStr(date) {
  if (!date) { date = new Date(); } 
  var dd = "" + date.getDate();
  if (dd.length === 1) { dd = '0' + dd; }
  var mm = "" + (date.getMonth() + 1);
  if (mm.length === 1) { mm = '0' + mm; }
  var s =  date.getFullYear() + '-' + lzero(date.getMonth()+1) + '-' + lzero(date.getDate());
  s +=  ' ' + lzero(date.getHours()) + ':' + lzero(date.getMinutes()) + ':' + lzero(date.getSeconds());
  return s;
}

// return ISO date: YYYY-MM-DD
function getISODateStr(date) {
  if (!date) { date = new Date(); } 
  return date.getFullYear() + '-' + lzero(date.getMonth()+1) + '-' + lzero(date.getDate());
}

function getDateStr(date) {
  // see: http://www.w3schools.com/jsref/jsref_obj_date.asp
  // return D.M.YYYY
  if (!date) { date = new Date(); }
  // .setDate(15), .setMonth(3), .setFullYear(2011)
  // increase date by 7 days: date.setDate(date.getDate() + 7)
  // decrease time by 5 hours:.date.setUTCHours( date.getUtcHours() - 4)
  var s = "";
  //s += daysOfWeek[date.getDay()] + " ";
  s += date.getDate() + '.' + (date.getMonth() + 1) + '.' + date.getFullYear();
  return s; 
}

function getShortDateStr(date) {
  // return e.g. Ut 13.2.
  if (!date) { date = new Date(); }
  var s = "";
  s += daysOfWeek[date.getDay()] + " ";
  s += date.getDate() + '.' + (date.getMonth() + 1) + '.';
  return s; 
}

function getDateFromISOStr(datestr) {
  // parse iso datestr, return Date instance; may be just 'return new Date(datestr)'' is enough?
  return new Date(Number(datestr.substr(0, 4)), Number(datestr.substr(5, 2))-1, Number(datestr.substr(8, 2)));
}
/*/ Date functions */

//http://stackoverflow.com/questions/246193/how-do-i-round-a-number-in-javascript
function roundNumber(number, digits) {
  var multiple = Math.pow(10, digits);
  var rndedNum = Math.round(number * multiple) / multiple;
  return rndedNum;
}


/* optional function arguments using object parameter method
   http://www.openjs.com/articles/optional_function_arguments.php
   Usage - e.g.:

   person({
    'name'	:	"George W. Bush",
    'me'	:	false,
    'site'	:	"miserable failure"
   });
*/
function person(options) {
  var i, index;
  var default_args = {
    'name':"Binny V A",
    'me':true,
    'site':"http://www.bin-co.com/",
    'species':"Homo Sapien"
  };
  for(index in default_args) {
    if(typeof options[index] == "undefined") options[index] = default_args[index];
  }
  /* options[] has all the data - user provided and optional */
  for(var i in options) {
    alert(i + " = " + options[i]);
  }
}

/* https://github.com/andyet/ConsoleDummy.js/blob/master/ConsoleDummy.js */
(function (con) {
    // the dummy function
    function dummy() {};
    // console methods that may exist
    for(var methods = "assert,count,debug,dir,dirxml,error,exception,group,groupCollapsed,groupEnd,info,log,markTimeline,profile,profileEnd,time,timeEnd,trace,warn".split(','), func; func = methods.pop();) {
        con[func] = con[func] || dummy;
    }
}(window.console = window.console || {}));
