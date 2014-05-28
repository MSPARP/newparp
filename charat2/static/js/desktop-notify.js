function desktopNotification(title,text,icon) {
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