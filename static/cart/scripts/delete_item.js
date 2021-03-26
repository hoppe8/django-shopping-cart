var url = $('#selection-form').attr('action');

document.getElementById("selection-form").addEventListener("click", function(event){
   item_id = event.target.parentElement.parentElement.id;
   if (item_id.slice(0,12) === "item-button-"){
      item_num = item_id.slice(12);

      $.ajax({
         type: "POST",
         url: url,
         data: { 
            'csrfmiddlewaretoken': $("input[name=csrfmiddlewaretoken]").val(),
            item_num: item_num,
	    action: "delete",
         },
         dataType: "json",
         success: function(result) {
	    location.reload(true);
         },
         error: function(result) {
            alert('error');
         }
      });

   }

});

