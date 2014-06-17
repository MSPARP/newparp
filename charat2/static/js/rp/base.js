var quotes = [
    'Oh god how did this get here I am not good with computer.',
    'Hello everybody! I hope you have a good day!',
    'uggghhhh..... What\'s with all this /green/???',
    'Green is my favorite color 0.0',
    'Hm.... I wonder where all my friends are...',
    'Chara just wished that I have a good time!',
    'Dang! It didn\'t work!',
    'Just little old me~',
    'I wonder what happened...',
    'I hope Charat works today!',
];

// History.js
(function(window,undefined){

    // Prepare
    var History = window.History; // Note: We are using a capital H instead of a lower h
    if ( !History.enabled ) {
         // History.js is disabled for this browser.
         // This is because we can optionally choose to support HTML4 browsers or not.
        return false;
    }

    // Bind to StateChange Event
    History.Adapter.bind(window,'statechange',function(){ // Note: We are using statechange instead of popstate
        var State = History.getState(); // Note: We are using History.getState() instead of event.state
        History.log(State.data, State.title, State.url);
    });

    // Change our States
    History.pushState({state:1}, "State 1", "?state=1"); // logs {state:1}, "State 1", "?state=1"
    History.pushState({state:2}, "State 2", "?state=2"); // logs {state:2}, "State 2", "?state=2"
    History.replaceState({state:3}, "State 3", "?state=3"); // logs {state:3}, "State 3", "?state=3"
    History.pushState(null, null, "?state=4"); // logs {}, '', "?state=4"
    History.back(); // logs {state:3}, "State 3", "?state=3"
    History.back(); // logs {state:1}, "State 1", "?state=1"
    History.back(); // logs {}, "Home Page", "?"
    History.go(2); // logs {state:3}, "State 3", "?state=3"

})(window);

$.fn.exists = function(){return this.length>0;}

function cmobile() {
    if (navigator.userAgent.indexOf('Android')!=-1 || navigator.userAgent.indexOf('iPhone')!=-1 || navigator.userAgent.indexOf('Nintendo 3DS')!=-1 || navigator.userAgent.indexOf('Nintendo DSi')!=-1 || window.innerWidth<=630) {
        return true;
    } else {
        return false;
    }
}

function screenCheck() {
    if (cmobile()){
        $(document.body).addClass('mobile');
        $(document.body).removeClass('nobile');
    } else if (window.innerWidth<=950){
        $(document.body).addClass('nobile');
        $(document.body).removeClass('mobile');
    } else  {
        $(document.body).removeClass('mobile');
        $(document.body).removeClass('nobile');
    }
}

$(document).ready(function() {
    var quote = quotes[Math.floor(Math.random()*quotes.length)];
    $('#quote').html(quote);

    if(navigator.userAgent.match(/(iPad|iPhone|iPod)/g) ? true : false) {
        $('meta[name=viewport]').attr('content', 'width=device-width, initial-scale=1, maximum-scale=1, user-scalable=no" />');
    }
    
    /* Topbar Menu */
    $('#toptitle').click(function() {
        if ($('body.menu').exists()) {
            $(document.body).removeClass('menu');
        } else {
            $(document.body).addClass('menu');
        }
    });
    $('#topbar').on("mouseleave", function(){
        if ($('body.menu').exists()) {
            $(document.body).removeClass('menu');
        }
    });
});

$(window).load(function() {
    screenCheck();
    $(window).resize(function() {
        screenCheck();
    });
});