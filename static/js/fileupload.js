
function getAcceptedExtension (input_id) {
  $('#' + input_id).attr('accept', '.jpg, .jpeg, .png').focus().click()
}

function readURL (input, img_id) {
  if (input.files && input.files[0]) {
    var reader = new FileReader()

    reader.onload = function (e) {
      $('#' + img_id).attr('src', e.target.result).width('100%')
    }
    reader.readAsDataURL(input.files[0])
  }
}
