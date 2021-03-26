$('#selection-form').keypress(function(event) {

   var code = (event.keyCode ? event.keyCode : event.which);
   if (!((code >= 48 && code <= 57) || (code == 13)))
   event.preventDefault();

});
