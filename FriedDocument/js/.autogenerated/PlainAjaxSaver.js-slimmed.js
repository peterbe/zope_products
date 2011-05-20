function ajaxSave(f){if(f.ajax_return.value!="1") return true;var d = $(f).serialize();$.post(f.action, d, function(response){id$('savechangesbutton').value='Save changes';var smsg=id$('savemessage');smsg.innerHTML = 'Changes saved';fadetext("savemessage");
hex=0;updateRevisionUndoer(f.slot.value);
reveal_validation_errors();});
return false;}