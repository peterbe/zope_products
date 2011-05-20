function AutoSuggest(elem,suggestions){var me=this;this.elem=elem;this.suggestions=suggestions;this.eligible=new Array();this.inputText=null;this.highlighted = -1;this.div=document.getElementById("autosuggest");var TAB=9;var ESC=27;var KEYUP=38;var KEYDN=40;elem.setAttribute("autocomplete","off");if(!elem.id){var id = "autosuggest" + idCounter;idCounter++;
elem.id=id;}

elem.onkeydown=function(ev)
{var key=me.getKeyCode(ev);switch(key)
{case TAB:
me.useSuggestion();break;
case ESC:
me.hideDiv();break;
case KEYUP:if(me.highlighted > 0){me.highlighted--;}
me.changeHighlight(key);break;
case KEYDN:if(me.highlighted < (me.eligible.length - 1)){me.highlighted++;}
me.changeHighlight(key);break;}};elem.onkeyup=function(ev) 
{var key=me.getKeyCode(ev);switch(key)
{case TAB:
case ESC:
case KEYUP:
case KEYDN:
return;default:if(this.value != me.inputText && this.value.length > 0){me.inputText=this.value;me.getEligible();
me.createDiv();me.positionDiv();
me.showDiv();}else{me.hideDiv();}}};this.useSuggestion=function(){if(this.highlighted > -1){this.elem.value=this.eligible[this.highlighted];this.hideDiv();
setTimeout("document.getElementById('" + this.elem.id + "').focus()",0);}};this.showDiv=function(){this.div.style.display = 'block';};

this.hideDiv=function(){this.div.style.display = 'none';this.highlighted = -1;};

this.changeHighlight=function(){var lis=this.div.getElementsByTagName('LI');for(i in lis){var li=lis[i];if(this.highlighted==i){li.className = "selected";}else{li.className = "";}}};this.positionDiv=function(){var el=this.elem;var x=0;var y=el.offsetHeight;while(el.offsetParent && el.tagName.toUpperCase()!='BODY'){x+=el.offsetLeft;y+=el.offsetTop;el=el.offsetParent;}
x+=el.offsetLeft;y+=el.offsetTop;this.div.style.left=x + 'px';this.div.style.top=y + 'px';};

this.createDiv=function(){var ul=document.createElement('ul');for(i in this.eligible){var word=this.eligible[i];var li=document.createElement('li');var a=document.createElement('a');a.href="javascript:false";
a.innerHTML=word;li.appendChild(a);if(me.highlighted==i){li.className = "selected";}
ul.appendChild(li);}
this.div.replaceChild(ul,this.div.childNodes[0]);ul.onmouseover=function(ev)
{var target=me.getEventSource(ev);while(target.parentNode && target.tagName.toUpperCase()!='LI'){target=target.parentNode;}
var lis=me.div.getElementsByTagName('LI');for(i in lis){var li=lis[i];if(li==target){me.highlighted=i;break;}}
me.changeHighlight();};

ul.onclick=function(ev)
{me.useSuggestion();me.hideDiv();
me.cancelEvent(ev);return false;};
this.div.className="suggestion_list";this.div.style.position = 'absolute';};

this.getEligible=function(){this.eligible=new Array();for(i in this.suggestions){var suggestion=this.suggestions[i];if(suggestion.toLowerCase().indexOf(this.inputText.toLowerCase())=="0"){this.eligible[this.eligible.length]=suggestion;}}};this.getKeyCode=function(ev)
{if(ev){return ev.keyCode;}if(window.event){return window.event.keyCode;}};this.getEventSource=function(ev)
{if(ev){return ev.target;}if(window.event){return window.event.srcElement;}};this.cancelEvent=function(ev)
{if(ev){ev.preventDefault();ev.stopPropagation();}if(window.event){window.event.returnValue=false;}}}
var idCounter=0;