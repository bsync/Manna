$(document).ready(function() {
    var max_fields = $("#upbox").data("maxcnt");
    var x = 1;
    $(".add_field").click(function(e) {
        e.preventDefault();
        if (x < max_fields) {
            x++;
            newunit = $(".upunit").last().clone(true)
            newunit.find('.fileselect').val("")
            var vname = newunit.find(".vidname").first()
            rmatch = (vname.val().match(/(\D*)(\d+$)/) || [])
            vname.val(rmatch[1] + (+rmatch[2] + 1))
            newunit.prepend("<hr><hr>")
            newunit.appendTo("#upbox")
        } else {
            alert(`Only ${max_fields} uploads at a time`)
        }
    });

    $(".del_field").click(function(e) {
        e.preventDefault();
        if (x > 1) {
           $(".upunit").last().remove();
           x--;
        }
    });
})

document.addEventListener('DOMContentLoaded', function() {
    var browse = $("#UploadForm_Submit")
    browse[0].addEventListener('click', handleFileSelect, false)
})

function handleFileSelect(evt) {
   evt.stopPropagation()
   evt.preventDefault()
   var ups = $.map($(".upunit"), function(upunit) { return upload(upunit) })
   $.when(...ups).done(function() { 
      $("#UploadForm").submit() 
   })
}

function upload(upunit) {
   var upfile = $(upunit).find(".fileselect")[0].files[0]
   var vidname = $(upunit).find(".vidname")[0].value
   var progbar = $(upunit).find(".progress")[0]
   var results = $(upunit).find(".status")[0]
   var vidout = $(upunit).find(".vidid")[0]
   var vimtoken = $("#accessToken")[0].value
   var tm=0, timer=setInterval(function(){tm++},1000);

   var upvimeo = new Promise((resolve,reject) => {
      new VimeoUpload({
         name: vidname,
         description: "TODO",
         private: false,
         file: upfile,
         token: vimtoken,
         upgrade_to_1080: true,
         onError: function(data) {
         showMessage(results, '<strong>Error</strong>: ' 
                     + JSON.parse(data).error, 'danger') },
         onProgress: function(data) {
            updateProgress(data.loaded / data.total, progbar) },
         onComplete: (vid) => { vidout.value = vid; resolve(vid) }
     }).upload()
   })

   function waitForTranscode(videoId) {
      showMessage(results, 
                  'Waiting for transcode to complete for: ' +
                  '<strong>' + upfile.name + '</strong>')
      return new Promise( 
         function (resolve, reject) { 
            (function pollTranscode(vidid) {
               var url = 'https://vimeo.com/' + vidid
               $.ajax({url: "https://api.vimeo.com/videos/" + vidid 
                         + "?fields=uri,upload.status,transcode.status",
                       type: "GET",
                       beforeSend: function(xhr) { 
                          xhr.setRequestHeader('Authorization', 
                                               'Bearer ' + vimtoken); }, 
                       success: function (resp) {
                           if (resp.transcode.status != "complete") {
                              showMessage(results, 
                                 'Transcode status after ' + tm + ' seconds: ' 
                                 + upfile.name + ' ' +
                                 '<strong>' + resp.transcode.status 
                                 + '</strong>' )
                              setTimeout(pollTranscode, 3000, vidid) }
                           else { 
                              showMessage(results, 
                                  'Transcode complete for: ' + 
                                  '<strong>' + upfile.name + '</strong>' +
                                  '</br> uploaded video @ ' + 
                                  '<a href="' + url + '">' + url + '</a>')
                              resolve(vidid) } }
               })
            })(videoId)
         }
      )
   }
   return upvimeo.then((videoId) => waitForTranscode(videoId))
}

function showMessage(results, html, type) {
   $(results).attr('class', 'alert alert-' + (type || 'success'))
   $(results).html(html)
}

function updateProgress(progress, bar) {
    progress = Math.floor(progress * 100)
    $(bar).attr('style', 'background-color: blue; width:' + progress + '%')
    $(bar).html('&nbsp;' + progress + '%')
}

