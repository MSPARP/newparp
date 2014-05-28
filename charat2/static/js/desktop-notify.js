function desktopNotification(title,text,icon) {
    try {
        var notification = new Notification(title, {
            body: text,
            icon: icon
        });
        notification.onclick = function() {
            try {
                window.blur();
                setTimeout(window.focus, 0);
                notification.close();
            } catch(e) {}
        };
        setTimeout(function(){
            try {
                notification.close();
            } catch(e) {}
        },5000);
        window.onbeforeunload = function(){
            try {
                notification.close();
            } catch(e) {}
        };
        window.addEventListener("focus", function(event) {
            try {
                notification.close();
            } catch(e) {}
        }, false);
    } catch(e) {
        
    }
}