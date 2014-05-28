function authorize() {
    Notification.requestPermission(function(e) {
        console.log(e);
    })
}

function show(title,text,icon) {
    var notification = new Notification(title, {
        dir: "auto",
        body: text,
        icon: icon
    });
    notification.onclick = function() {
        
    }
    setTimeout(function(){
        try {
            notification.close();
        } catch(e) {}
    },5000);
}