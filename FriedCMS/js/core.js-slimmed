function addEvent(obj,type,fn){if( obj.attachEvent ){obj["e"+type+fn] = fn;obj[type+fn] = function(){obj["e"+type+fn]( window.event );}
obj.attachEvent( "on"+type, obj[type+fn] );} else
obj.addEventListener(type,fn,false);}
function removeEvent(obj,type,fn){if( obj.detachEvent ){obj.detachEvent( "on"+type, obj[type+fn] );obj[type+fn] = null;} else
obj.removeEventListener(type,fn,false);}
function econvert(s){return s.replace(/%7E/g,'~').replace(/%28/g,'(').replace(/%29/g,')').replace(/%20/g,' ').replace(/_dot_| dot |_\._|\(\.\)/gi, '.').replace(/_at_|~at~/gi, '@');}
function AEHit(){var sp=document.getElementsByTagName("span");for(i=0;i< sp.length;i++)if(sp[i].className=="aeh") 
sp[i].innerHTML=econvert(sp[i].innerHTML);}
addEvent(window, 'load', AEHit);function $(){var elements=new Array();for(var i=0;i < arguments.length;i++){var element=arguments[i];if(typeof element == 'string')
element=document.getElementById(element);if(arguments.length==1) 
return element;elements.push(element);}
return elements;}