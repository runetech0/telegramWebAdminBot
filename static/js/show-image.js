function readURL(input) {
    if (input.files && input.files[0]) {
        var reader = new FileReader();

        reader.onload = function (e) {
            $('#uploadedImage')
                .attr('src', e.target.result)
                .width(500)
                .height(300);
            $('#uploadedImage').removeAttribute('hidden')
        };

        reader.readAsDataURL(input.files[0]);
    }
}