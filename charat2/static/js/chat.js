/* FINAL VARIABLES */

var SEARCH_PERIOD = 1;
var PING_PERIOD = 10;

var POST_URL = "/chat_ajax/post";
var SAVE_URL = "/chat_api/save";

var CHAT_PING = '/chat_api/ping';
var CHAT_MESSAGES = '/chat_api/messages';
var CHAT_QUIT = '/chat_api/quit';

var CHAT_FLAGS = ['autosilence','public','nsfw'];

var MOD_GROUPS = ['globalmod', 'mod', 'mod2', 'mod3'];
var GROUP_RANKS = { 'globalmod': 6, 'mod': 5, 'mod2': 4, 'mod3': 3, 'user': 2, 'silent': 1 };
var GROUP_DESCRIPTIONS = {
    'globalmod': { title: 'Adoraglobal Mod', description: 'Charat Staff' },
    'mod': { title: 'Magical Mod', description: 'Silence, Kick and Ban' },
    'mod2': { title: 'Cute-Cute Mod', description: 'Silence and Kick' },
    'mod3': { title: 'Little Mod', description: 'Silence' },
    'user': { title: '', description: '' },
    'silent': { title: 'Silenced', description: '' },
};

var ORIGINAL_TITLE = document.title;
var CHAT_NAME = chat['title'] || chat.url;
var CONVERSATION_CONTAINER = '#conversation';
var CONVERSATION_ID = '#convo';
var MISSED_MESSAGE_COUNT_ID = '#exclaim';
var USER_LIST_ID = '#online';

/* VARIABLES */

var window_active;
window.onfocus = function () {
   window_active = true;
};
window.onblur = function () {
   window_active = false;
};

var chat_state = 'chat';
var user_state = 'online';

var current_sidebar = null;

var hidden, visibilityChange;
if (typeof document.hidden !== "undefined") {
    hidden = "hidden";
    visibilityChange = "visibilitychange";
} else if (typeof document.mozHidden !== "undefined") {
    hidden = "mozHidden";
    visibilityChange = "mozvisibilitychange";
} else if (typeof document.msHidden !== "undefined") {
    hidden = "msHidden";
    visibilityChange = "msvisibilitychange";
} else if (typeof document.webkitHidden !== "undefined") {
    hidden = "webkitHidden";
    visibilityChange = "webkitvisibilitychange";
}

var ooc_on = false; // USER META ADD
var preview_show = false; // USER META ADD
var confirm_disconnect = user.meta.confirm_disconnect;
var desktop_notifications = user.meta.desktop_notifications;
var show_bbcode = user.meta.show_bbcode;
var show_bbcode_color = true; // USER META ADD
var show_description = user.meta.show_description;
// Show and Hide different message types
var show_system_messages = user.meta.show_system_messages;

/* FUNCTIONS */

function topbarSelect(selector) {
    $(selector).css({
        'color' : '#C0F0C0',
    });
}

function topbarDeselect(selector) {
    $(selector).css({
        'color' : ''
    });
}

function isChecked(id) {
    var checked = $("input[@id=" + id + "]:checked").length;
    if (checked == 0) {
        return false;
    } else {
        return true;
    }
}

function startChat() {
    $(CONVERSATION_CONTAINER).scrollTop($(CONVERSATION_CONTAINER).prop("scrollHeight"));
    if (!$(document.body).hasClass('mobile')) {
        $("#textInput").focus();
    }
    var crom = $(CONVERSATION_CONTAINER).scrollTop()+$(CONVERSATION_CONTAINER).height()+24;
    var den = $(CONVERSATION_CONTAINER).prop("scrollHeight");
    $(window).resize(function(e) {
        var lon = den-crom;
        if (lon <= 50){
            $(CONVERSATION_CONTAINER).scrollTop($(CONVERSATION_CONTAINER).prop("scrollHeight"));
        }
    });
    document.title = (chat['title'] || chat.url)+' - '+ORIGINAL_TITLE;
    if (chat.type=='unsaved' || chat.type=='saved') {
        document.title = ORIGINAL_TITLE+' - '+chat.url;
    }
    msgcont = 0;
    $(CONVERSATION_CONTAINER).removeClass('search');
    $('input, select, button').removeAttr('disabled');
    $('#preview').css('color', '#'+user.character.color);
    $('#logLink').attr('href', '/chat/'+chat.url+'/log');
    
    if ($(document.body).hasClass('mobile')) {
        var current_sidebar = null;
    } else {
        var current_sidebar = "userList";
    }
    if (!current_sidebar) {
        setSidebar(null);
    } else {
        setSidebar(current_sidebar);
    }
    //getMeta();
    getMessages();
    pingInterval = window.setTimeout(pingServer, PING_PERIOD*1000);
    updateChatPreview();
}

function addLine(msg){
	// MAKE A CONVERSATION SCROLL FUNCTION
    var von = $(CONVERSATION_CONTAINER).scrollTop()+$(CONVERSATION_CONTAINER).height()+24;
    var don = $(CONVERSATION_CONTAINER).prop("scrollHeight");
    var lon = don-von;
    if (lon <= 30){
        flip = 1;
    } else {
      $(MISSED_MESSAGE_COUNT_ID).html(parseInt($(MISSED_MESSAGE_COUNT_ID).html())+1);
    }

    if (show_bbcode_color == true) {
        message = bbEncode(htmlEncode(msg.text));
    } else {
        message = bbEncode(htmlEncode(bbRemove(msg.text)));
    }

    msgClass = msg.type;
    var alias = "";
    if (msg.acronym) {
        alias = msg.acronym+": ";
    }

    var mp = $('<p>').attr("id","message"+msg.id).addClass(msg.type).addClass("user"+msg.user_id).css('color', '#'+msg.color).html(alias+message).appendTo(CONVERSATION_ID);

    if (flip == 1) {
        $(CONVERSATION_CONTAINER).scrollTop($(CONVERSATION_CONTAINER).prop("scrollHeight"));
        flip = 0;
    }

    if (window_active == false && desktop_notifications == true) {
        show(chat.url,htmlEncode(bbRemove(msg.text)));
    }
    shownotif = 0;
}

function generateUserList(user_data) {
    $(USER_LIST_ID).empty();
    for (var i=0; i<user_data.length; i++) {
        list_user = user_data[i];
        $(USER_LIST_ID).append('<li id="user'+list_user.meta.user_id+'"><span class="userCharacter"  style="color:#'+list_user.character.color+';">'+list_user.character.name+' ['+list_user.character.acronym+']</span><span class="username">'+list_user.meta.username+'</span></li>');
    }
    // test
}

function getMessages() {
    var messageData = {'chat_id': chat['id'], 'after': latestNum};
    $.post(CHAT_MESSAGES, messageData, function(data) {
        messageParse(data);
    }, "json").complete(function() {
        if (chat_state=='chat') {
            window.setTimeout(getMessages, 50);
        } else {
            // Disconnected methods
        }
    });
}

function pingServer() {
    $.post(CHAT_PING, {'chat_id': chat['id']});
    pingInterval = window.setTimeout(pingServer, PING_PERIOD*1000);
    updateChatPreview();
}

function messageParse(data) {
	// KICK/BAN RECEIVAL
    /* if (typeof data.exit!='undefined') {
        if (data.exit=='kick') {
            clearChat();
            addLine({ counter: -1, color: '000000', text: 'You have been kicked from this chat. Please think long and hard about your behaviour before rejoining.' });
        } else if (data.exit=='ban') {
            latestNum = -1;
            chat = 'theoubliette'
            $('#userList h1')[0].innerHTML = 'theoubliette';
            $(CONVERSATION_CONTAINER).empty();
        }
        return true;
    } */
    var messages = data.messages;
    for (var i=0; i<messages.length; i++) {
        addLine(messages[i]);
        latestNum = Math.max(latestNum, messages[i]['id']);
    }
    if (typeof data.counter!="undefined") {
        user.meta.counter = data.counter;
    }
    if (typeof data.users!=="undefined") {
        generateUserList(data.users);
    }
    if (typeof data.meta!='undefined') {
        // Reload chat metadata.
        var chat = data.meta;

        for (i=0; i<CHAT_FLAGS.length; i++) {
            if (typeof data.meta[CHAT_FLAGS[i]]!='undefined') {
                $('#'+CHAT_FLAGS[i]).attr('checked', 'checked');
                $('#'+CHAT_FLAGS[i]+'Result').show();
            } else {
                $('#'+CHAT_FLAGS[i]).removeAttr('checked');
                $('#'+CHAT_FLAGS[i]+'Result').hide();
            }
        }

        if (typeof data.meta.topic!='undefined') {
            $('#topic').html(bbEncode(data.meta.topic));
        } else {
            $('#topic').text('');
        }

        if (user.meta.group == 'mod' || user.meta.group == 'globalmod') {
            $('.inPass').hide();
            $('.editPass').show();
        } else {
            $('.editPass').hide();
            $('.inPass').show();
        }
        //NSFW
        if (data.meta['nsfw'] == '1') {
            //Change
        } else {
            //Changed
        }
    }
    if (messages.length>0 && typeof hidden!="undefined" && document[hidden]==true) {

    }
    if (user.meta.group == 'mod' || user.meta.group == 'globalmod') {
        $('.inPass').hide();
        $('.editPass').show();
        $('.opmod input').removeAttr('disabled');
    } else {
        $('.editPass').hide();
        $('.inPass').show();
        $('.opmod input').attr('disabled', 'disabled');
    }
}

function disconnect() {
    if (confirm('Are you sure you want to disconnect?')) {
        $.ajax(CHAT_QUIT, {'type': 'POST', data: {'chat_id': chat['id']}});
        clearChat();
    }
}

function clearChat() {
    chat_state = 'inactive';
    if (pingInterval) {
        window.clearTimeout(pingInterval);
    }
    $('input[name="chat"]').val(chat.url);
    $('input, select, button').attr('disabled', 'disabled');
    setSidebar(null);
    document.title = (chat['title'] || chat.url)+' - '+ORIGINAL_TITLE;
    if (chat.type=='unsaved' || chat.type=='saved') {
        document.title = ORIGINAL_TITLE+' - '+chat.url;
    }
    msgcont = 0;
}

function setSidebar(sidebar) {
    $('.sidebar').hide();
    topbarDeselect('#topbar .right span');
    current_sidebar = sidebar;
    if (current_sidebar) {
        $('#'+current_sidebar).show();
        topbarSelect('#topbar .right .'+current_sidebar);
        $(document.body).addClass('withSidebar');
    } else {
        $(document.body).removeClass('withSidebar');
    }

    // if sidebar changed, check bottom and go to bottom if at bottom
}

function closeSettings() {
    //findit
    if ($(document.body).hasClass('mobile')) {
        if (navigator.userAgent.indexOf('Nintendo 3DS')!=-1 || navigator.userAgent.indexOf('Nintendo DSi')!=-1) {} {
            setSidebar(null);
        }
    } else {
        setSidebar('userList');
    }
}

function readCookie(name) {
    var nameEQ = name + "=";
    var ca = document.cookie.split(';');
    for(var i=0;i < ca.length;i++) {
        var c = ca[i];
        while (c.charAt(0)==' ') c = c.substring(1,c.length);
        if (c.indexOf(nameEQ) == 0) return c.substring(nameEQ.length,c.length);
    }
    return null;
}

function updateChatPreview(){
    var textPreview = $('#textInput').val().replace(/\r\n|\r|\n/g,"[br]");
    
    if ($('#textInput').val().substr(0,1)=='/') {
        textPreview = textPreview.substr(1);
    } else {
        textPreview = applyQuirks(textPreview);
    }
    
    textPreview = jQuery.trim(textPreview);
    
    if (textPreview.length>0) {
        $('#preview').text(textPreview);
    } else {
        $('#preview').html('&nbsp;');
    }
    $(CONVERSATION_CONTAINER).css('bottom',($('.controls').height()+20)+'px');
    return textPreview.length!=0;
    // Hide if typing at bottom
}

function previewToggle() {
    if (!preview_show) {
         $('#preview').show();
    } else {
        $('#preview').hide();
    }
    updateChatPreview();
    preview_show = !preview_show;
}

// CHANGE THE SETTINGS IN THE CHAT.HTML with {% %}
// CHANGE THE SETTINGS WITH AJAX REQUEST ON BUTTON CLICKS
// BBCODE REWRITE + REMEMBER TO GO THROUGH ALL PREVIOUS MESSAGES AND BBCODE THEM
// CHECK IF COOKIES ARE ENABLED

// REWRITE USERLIST AND ADD IN NEW HIGHLIGHTING AND BLOCKING SCRIPTS

// ADD NEW MESSAGE HIDING

// SPLIT MESSAGE IF MESSAGE IS TOO LONG?

// CUSTOM ALERTS, NO MORE alert();

// PUT LINKIFY INTO THE BBCODE FUNCTION AS WELL AS HTML TO TEXT

$(document).ready(function() {
    if (document.cookie=="") {
        // NOTIFY USER THAT THEY CAN'T CHAT WITHOUT COOKIES
    } else {

        /* START UP */
        startChat();
        
        $('#ooclet, #oocToggle input').click(function() {
            if (ooc_on == false) {
                ooc_on = true;
                $('#oocToggle input').attr('checked','checked');
                topbarSelect('#ooclet');
            } else {
                ooc_on = false;
                $('#oocToggle input').removeAttr('checked');
                topbarDeselect('#ooclet');
            }
            updateChatPreview();
        });
        
        $('#topbar .right span').click(function() {
            if ($(this).attr('class') == current_sidebar) {
                current_sidebar = null;
                setSidebar(current_sidebar);
            } else {
                current_sidebar = $(this).attr('class');
                setSidebar(current_sidebar);
            }
        });
        
        /* SUBMISSION AND ACTIVE CHANGES */
        $('.controls').submit(function() {
            $('#textInput').focus();
            if (updateChatPreview()) {
                if (jQuery.trim($('#textInput').val())=='/ooc') {
                    ooc_on = true;
                    topbarSelect('#ooclet');
                    $('#oocToggle input').attr('checked','checked');
                    $('#textInput').val('');
                    return false;
                } else if (jQuery.trim($('#textInput').val())=='/ic') {
                    ooc_on = false;
                    topbarDeselect('#ooclet');
                    $('#oocToggle input').removeAttr('checked');
                    $('#textInput').val('');
                    return false;
                }
                
                if ($('#textInput').val().charAt(0)=='/') {
                    var command = $('#textInput').val().split(' ');
                    if (command[0] == '/set') {
                        var groups = ['magical','cute','little','unsilence','silence'];
                        if (MOD_GROUPS.indexOf(command[2].toLowerCase())!=-1) {
                            alert('Setting '+command[1]+" to "+command[2]);
                        }
                    }
                }
                
                if ($('#textInput').val()!='') {
                    if (pingInterval) {
                        window.clearTimeout(pingInterval);
                    }
                    var lineSend = $('#preview').text();
                    $.post('/chat_api/send',{'chat_id': chat['id'], 'text': lineSend}); // todo: check for for error
                    pingInterval = window.setTimeout(pingServer, PING_PERIOD*1000);
                    $('#textInput').val('');
                    updateChatPreview();
                }
            }
            if ($(document.body).hasClass('mobile')) {} else {
                $("#textInput").focus();
            }
            $('#textInput').val('');
            return false;
        });

        $('#textInput').change(updateChatPreview).keyup(updateChatPreview).change();

        /* $("#textInput").on('keydown', function() {
            var num = 1489;
            if ($('#preview').html().length > num) {
                values = $(this).val();
                values = values.substr(0,num+3);
                $(this).val(values);
            }
        }); */

        $("textarea#textInput").on('keydown', function(e) {
            if (!$(document.body).hasClass('mobile')) {
                if (e.keyCode == 13 && !e.shiftKey)
                {
                    e.preventDefault();
                    $('.controls').submit();
                }
            }
        });
        
        $("#statusInput").on('keydown', function(e) {
            if (e.keyCode == 13) {
                $('#statusButton').click();
            }
        });

        // MAKE PREVIEW A SETTING, DEFAULT OFF
        $('#previewToggle input').click(function() {
            preview_show != preview_show;
            previewToggle();
        });
        
        $('#disconnectButton').click(disconnect);

        $('#statusButton').click(function() {
            new_state = $('#statusInput').val();
            $('#statusInput').val('');
            $.post(POST_URL, {'chat_id': chat['id'], 'state': new_state}, function(data) {
                user_state = new_state;
            });
        });

        $('#settings').submit(function() {
            // Trim everything first
            formInputs = $('#settings').find('input, select');
            for (i=0; i<formInputs.length; i++) {
                formInputs[i].value = jQuery.trim(formInputs[i].value)
            }
            if ($('input[name="name"]').val()=="") {
                alert("You can't chat with a blank name!");
            } else if ($('input[name="color"]').val().match(/^[0-9a-fA-F]{6}$/)==null) {
                alert("You entered an invalid hex code. Try using the color picker.");
            } else {
                var formData = $(this).serializeArray();
                formData.push({ name: 'chat_id', value: chat['id'] })
                $.post(SAVE_URL, formData, function(data) {
                    $('#preview').css('color', '#'+$('input[name="color"]').val());
                    var formInputs = $('#settings').find('input, select');
                    for (i=0; i<formInputs.length; i++) {
                        if (formInputs[i].name!="quirk_from" && formInputs[i].name!="quirk_to") {
                            user.character[formInputs[i].name] = formInputs[i].value;
                        }
                    }
                    user.character.replacements = [];
                    var replacementsFrom = $('#settings').find('input[name="quirk_from"]');
                    var replacementsTo = $('#settings').find('input[name="quirk_to"]');
                    for (i=0; i<replacementsFrom.length; i++) {
                        if (replacementsFrom[i].value!="" && replacementsFrom[i].value!=replacementsTo[i].value) {
                            user.character.replacements.push([replacementsFrom[i].value, replacementsTo[i].value])
                        }
                    }
                    closeSettings();
                });
            }
            return false;
        });
        
        $('#metaOptions input').click(function() {
            var data = {'chat_id': chat['id'], 'meta_change': ''}
            // Convert to integer then string.
            data[this.id] = +this.checked+'';
            $.post(POST_URL, data);
        });
        
        // NEW TOPIC CHANGE FUNCTION
        
        $('.hidedesc').click(function() {
            if (topicHidden) {
                topichide = 0;
                $('#topic').show();
            } else {
                topichide = 1;
                $('#topic').hide();
            }
            topicHidden = !topicHidden;
            return false;
        });
        
        $(CONVERSATION_CONTAINER).scroll(function(){
            var von = $(CONVERSATION_CONTAINER).scrollTop()+$(CONVERSATION_CONTAINER).height()+24;
            var don = $(CONVERSATION_CONTAINER).prop("scrollHeight");
            var lon = don-von;
            if (lon <= 30){
                $(MISSED_MESSAGE_COUNT_ID).html(0);
            }
        });

        $('#extain').click(function(){
            $(MISSED_MESSAGE_COUNT_ID).html(0);
            $(CONVERSATION_CONTAINER).scrollTop($(CONVERSATION_CONTAINER).prop("scrollHeight"));
        });

        /* SPOILER
        $('#conversation p .spoiler').on('click', function() {
            if ($(this).css('opacity') == '0') {
                $(this).css('opacity','1');
            } else {
                $(this).css('opacity','0');
            }
        });
        */
        
        window.onbeforeunload = function (e) {
            if (confirm_disconnect == true) {
                if (chat_state=='chat') {
                    if (typeof e!="undefined") {
                        e.preventDefault();
                    }
                    return 'Are you sure you want to leave? Your chat is still running.';
                }
            }
        }
        
        $(window).unload(function() {
            $.ajax('/chat_api/quit', {'type': 'POST', data: {'chat_id': chat['id']}, 'async': false});
        });
    }
});

