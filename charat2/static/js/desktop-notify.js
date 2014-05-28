var guid = (function() {
  function s4() {
    return Math.floor((1 + Math.random()) * 0x10000)
               .toString(16)
               .substring(1);
  }
  return function() {
    return s4() + s4() + '-' + s4() + '-' + s4() + '-' +
           s4() + '-' + s4() + s4() + s4();
  };
})();

function desktopNotification(title,text,icon) {
    var notification = new Notification(title, {
        body: text,
        icon: icon,
        tag: guid()
    });
    notification.onclick = function() {
        
    }
    setTimeout(function(){
        try {
            notification.close();
        } catch(e) {}
    },5000);
}