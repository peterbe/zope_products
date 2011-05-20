function prepareDivTag(element){element.onclick=function(event){if(this.className!='highlight')
this.className='highlight';else
this.className='nothighlight';};}
function findDivTags(){var divs=document.getElementsByTagName('DIV');for(var i=0,len=divs.length;i<len; i++)if(divs[i].getAttribute('id') && divs[i].getAttribute('id').match(/faq\d\d/))
prepareDivTag(divs[i]);}
function main(){findDivTags();}
$(function(){findDivTags();});