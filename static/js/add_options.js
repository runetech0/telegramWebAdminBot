$(document).ready(function () {
  var option = 0;
  $("#add").click(function () {
    var lastField = $("#buildyourform div:last");
    var intId =
      (lastField && lastField.length && lastField.data("idx") + 1) || 1;
    var fieldWrapper = $('<div class="fieldwrapper" id="field' + intId + '"/>');
    fieldWrapper.data("idx", intId);
    var fName = $(
      `<input placeholder="Option${intId}" name="option${intId}" type="text" class="fieldname form-control d-inline-block" />`
    );
    var fType = $(
      '<select class="fieldtype"><option value="checkbox">Checked</option><option value="textbox">Text</option><option value="textarea">Paragraph</option></select>'
    );
    var removeButton = $(
      `<input type="button" class="remove btn btn-small btn-outline-dark my-2 d-inline-block" value="x" />`
    );
    removeButton.click(function () {
      $(this).parent().remove();
    });
    fieldWrapper.append(fName);
    // fieldWrapper.append(fType);
    fieldWrapper.append(removeButton);
    $("#buildyourform").append(fieldWrapper);
  });
  $("#preview").click(function () {
    $("#yourform").remove();
    var fieldSet = $(
      '<fieldset id="yourform"><legend>Your Form</legend></fieldset>'
    );
    $("#buildyourform div").each(function () {
      var id = "input" + $(this).attr("id").replace("field", "");
      var label = $(
        '<label for="' +
          id +
          '">' +
          $(this).find("input.fieldname").first().val() +
          "</label>"
      );
      var input;
      switch ($(this).find("select.fieldtype").first().val()) {
        case "checkbox":
          input = $(
            '<input type="checkbox" id="' + id + '" name="' + id + '" />'
          );
          break;
        case "textbox":
          input = $('<input type="text" id="' + id + '" name="' + id + '" />');
          break;
        case "textarea":
          input = $('<textarea id="' + id + '" name="' + id + '" ></textarea>');
          break;
      }
      fieldSet.append(label);
      fieldSet.append(input);
    });
    $("body").append(fieldSet);
  });
});
