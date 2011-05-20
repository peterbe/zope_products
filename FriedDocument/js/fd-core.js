function html_quote(s) {
   return s.replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');
}
function id$() {
  var elements = new Array();
  for (var i=0; i < arguments.length; i++) {
    var element = arguments[i];
    if (typeof element == 'string')
      element=document.getElementById(element);
    if (arguments.length == 1)
      return element;
    elements.push(element);
  }
  return elements;
}

function updateRevisionUndoer(slotname) {
   if ($('#revisionundoer')) {
      $('#revisionundoer').load('show_revision_undo_form', {currentslotname:slotname});
   }
}

function reveal_validation_errors() {
   $.post('getValidationError', function(result) {
      if (result) {
         if ($('#validationerror')) {
            $('#validationerror')
              .css('border','1px solid red').css('background','#fdd').css('padding','2px 6px')
              .show()
                .text(result);
            
         } else {
            alert("VALIDATION ERROR: " + ajax.response);
         }
      } else {
         $('#validationerror').hide();
      }
   });
   $('#validationerror').load('getValidationError');
   return;
}

function fadetext(id, hex){
   var o = id$(id);
   if (arguments.length==1) {
      o.style.color="rgb(0,0,0)";
      hex =0;
   }
   if(hex<255) {
      o.style.color="rgb("+hex+","+hex+","+hex+")";
      setTimeout("fadetext('"+id+"',"+(hex+5)+")",20);
   } else
     o.style.color="rgb(255,255,255)";
}