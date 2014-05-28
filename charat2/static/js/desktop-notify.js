function authorize() {
    Notification.requestPermission(function(e) {
        console.log(e);
    })
}

function show(title,text) {
    var notification = new Notification(title, {
        dir: "auto",
        lang: "",
        body: text,
    });
    notification.onclick = function() {
        
    }
}