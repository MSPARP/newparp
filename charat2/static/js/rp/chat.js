/* FINAL VARIABLES */

var SEARCH_PERIOD = 1;
var PING_PERIOD = 10;

var USER_ACTION_URL = '/chat_api/user_action';
var SET_GROUP_URL = '/chat_api/set_group';
var SET_TOPIC_URL = '/chat_api/set_topic';
var SET_FLAG_URL = '/chat_api/set_flag';

var SAVE_URL = '/chat_api/save';

var CHAT_PING = '/chat_api/ping';
var CHAT_MESSAGES = '/chat_api/messages';
var CHAT_QUIT = '/chat_api/quit';

var CHAT_FLAGS = ['autosilence','publicity','nsfw'];
var CHAT_FLAG_MAP = {
    'autosilence':true,
    'publicity':'listed',
    'nsfw':true
};

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

var ORIGINAL_TITLE = "Charat RP";
var CHAT_NAME = chat['title'] || chat.url;
var CONVERSATION_CONTAINER = '#conversation';
var CONVERSATION_ID = '#convo';
var MISSED_MESSAGE_COUNT_ID = '#exclaim';
var USER_LIST_ID = '#online';

/* VARIABLES */

var window_active;

var missed_messages = 0;

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
var show_all_info = true; // USER META ADD

var current_user_array = [];
var user_list = {};

var type_force = '';
var sending_line = '';

/* FUNCTIONS */

if (typeof String.prototype.startsWith != 'function') {
  String.prototype.startsWith = function (str){
    return this.slice(0, str.length) == str;
  };
}

if (typeof String.prototype.endsWith != 'function') {
  String.prototype.endsWith = function (str){
    return this.slice(-str.length) == str;
  };
}

function getTimestamp(seconds_from_epoch) {
    var month_names = ["Jan", "Feb", "Mar", "Apr", "May", "Jun","Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
    var timestamp = new Date(seconds_from_epoch*1000);
    return month_names[timestamp.getMonth()]+' '+timestamp.getDate()+' '+(timestamp.getHours()==0?'0':'')+timestamp.getHours()+':'+(timestamp.getMinutes()<10?'0':'')+timestamp.getMinutes();
}

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
    msgcont = 0;
    $(CONVERSATION_CONTAINER).removeClass('search');
    $('input, select, button').removeAttr('disabled');
    $('#preview').css('color', '#'+user.character.color);
    
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
    goBottom(CONVERSATION_CONTAINER);
    updateChatPreview();
}

function atBottom(element) {
    var von = $(element).scrollTop()+$(element).height()+24;
    var don = $(element).prop("scrollHeight");
    var lon = don-von;
    if (lon <= 30){
        return true;
    } else {
      return false;
    }
}

function goBottom(element) {
    $(element).scrollTop($(element).prop("scrollHeight"));
}

function addLine(msg){
    if (msg) {
        var at_bottom = atBottom(CONVERSATION_CONTAINER);
        if (!at_bottom) {
            $(MISSED_MESSAGE_COUNT_ID).html(parseInt($(MISSED_MESSAGE_COUNT_ID).html())+1);
        }
    
        if (show_bbcode_color == true) {
            message = bbEncode(msg.text);
        } else {
            message = bbEncode(bbRemove(msg.text));
        }
    
        var alias = "";
        if (msg.acronym) {
            alias = msg.acronym+": ";
        }
    
        if ($(CONVERSATION_CONTAINER+' p:last').hasClass("user"+msg.user_id) && $(CONVERSATION_CONTAINER+' p:last').hasClass('ic') && msg.type == 'ic') {
            $(CONVERSATION_CONTAINER+' p:last').hide();
        }
    
        var left_text = msg.type;
        if (msg.name) {
            if (msg.type == 'ic') {
                left_text = msg.name;
            } else {
                left_text = msg.name+':'+msg.type;
            }
        }
    
        var right_text = '<span class="username">'+msg.user.username+'</span> <span class="post_timestamp">'+getTimestamp(msg.posted)+'<span>';
        
        var message_container = $('<span>').prop("id","message"+msg.id).addClass(msg.type).addClass("user"+msg.user.id).appendTo(CONVERSATION_ID);
        var info = $('<p>').addClass("info").appendTo("#message"+msg.id);
        var info_left = $('<span>').addClass("left").html(left_text).appendTo("#message"+msg.id+" .info");
        var info_right = $('<span>').addClass("right").html(right_text).appendTo("#message"+msg.id+" .info");
        if (msg.type == 'me') {
            var message = $('<p>').addClass("message").html("<span style=\"color: #"+msg.color+";\">"+msg.name+"</span>"+" "+"[<span style=\"color: #"+msg.color+";\">"+msg.acronym+"</span>]"+" "+message).appendTo("#message"+msg.id);
        } else {
            var message = $('<p>').addClass("message").css('color', '#'+msg.color).html(alias+message).appendTo("#message"+msg.id);
        }
        
        if (at_bottom) {
            goBottom(CONVERSATION_CONTAINER);
            at_bottom = false;
        }
        
        if (window_active == false) {
            missed_messages++;
            if (missed_messages !=0) {
                document.title = missed_messages+" new – "+chat.title;
            }
        }
        
        if (window_active == false && desktop_notifications == true) {
            show(chat.url,htmlEncode(bbRemove(msg.text)));
        }
        shownotif = 0;
    }
}

function generateUserList(user_data) {
    for (var i=0; i<user_data.length; i++) {
        var list_user = user_data[i];
        var is_self = "";
        if (list_user.meta.user_id == user.meta.user_id) {
            is_self = " self";
            $('#online').prop('class',list_user.meta.group);
        }
        
        if ($('#user'+list_user.meta.user_id).length <= 0) {
            $(USER_LIST_ID).append('<li id="user'+list_user.meta.user_id+'" class="'+list_user.meta.username+'"><span class="userCharacter'+is_self+' '+list_user.meta.group+'"  style="color:#'+list_user.character.color+';">'+list_user.character.name+'</span><span class="username">'+list_user.meta.username+'</span></li>');
    
            var user_buttons = '<span class="set">' +
                    '<li class="mod">Make Magical Mod</li>' +
                    '<li class="mod2">Make Cute-Cute Mod</li>' +
                    '<li class="mod3">Make Little Mod</li>' +
                    '<li class="silent">Silence</li>' +
                    '<li class="unsilent">Unsilence</li>' +
                    '<li class="user">Remove Mod Status</li>' +
                '</span>' +
                '<span class="user_action">' +
                    '<li class="kick">Kick</li>' +
                    '<li class="ban">Ban</li>' +
                '</span>' +
                '<span class="chat_action">' +
                    '<li class="block">Block</li>' +
                    '<li class="highlight">Highlight</li>' +
                '</span>';
    
            $('#user'+list_user.meta.user_id).append('<ul class="user_buttons '+list_user.meta.group+'"></ul>');
            $('#user'+list_user.meta.user_id+' .user_buttons').append(user_buttons);
            user_list[list_user.meta.user_id] = list_user;
            user_list[list_user.meta.username] = list_user;
            
            $('.user_buttons').hide();
            $('#user'+list_user.meta.user_id).on('click', function() {
                var buttons_shown = $(this).find('.user_buttons').is(':visible');
                $('.user_buttons').hide();
                if (buttons_shown) {
                    $(this).find('.user_buttons').hide();
                } else {
                    $(this).find('.user_buttons').show();
                }
            });
        }
    }

    $(USER_LIST_ID+" .username").each(function() {
        var in_list = false;
        for (var i=0; i<user_data.length; i++) {
            if ($(this).text() == user_data[i].meta.username) {
                in_list = true;
            }
        }
        if (in_list) {
            $(this).parent().show();
        } else {
            $(this).parent().hide();
        }
    });
}

function userAction(user,action,reason) {
    var actionData = {'chat_id': chat.id, 'action': action, 'username': user, 'reason': reason};
    $.post(USER_ACTION_URL,actionData);
}

function setGroup(user,group) {
    var actionData = {'chat_id': chat.id, 'group': group, 'username': user};
    $.post(SET_GROUP_URL,actionData);
}

function setTopic(topic) {
    var actionData = {'chat_id': chat.id, 'topic': topic};
    $.post(SET_TOPIC_URL,actionData);
}

function setFlag(flag,val) {
    var actionData = {'chat_id': chat.id, 'flag': flag, 'value': val};
    $.post(SET_FLAG_URL,actionData);
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
    if (typeof data.exit!='undefined') {
        if (data.exit=='kick') {
            clearChat();
            addLine({ counter: -1, color: '000000', text: 'You have been kicked from this chat. Please think long and hard about your behaviour before rejoining.' });
        } else if (data.exit=='ban') {
			clearChat();
            window.location.replace('/chat/theoubliette');
        }
        return true;
    }
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
    if (typeof data.chat!='undefined') {
        // Reload chat metadata.
        var chat = data.chat;
        
        for (i=0; i<CHAT_FLAGS.length; i++) {
            if (data.chat[CHAT_FLAGS[i]] == CHAT_FLAG_MAP[CHAT_FLAGS[i]]) {
                $('#'+CHAT_FLAGS[i]).prop('checked', 'checked');
                $('#'+CHAT_FLAGS[i]+'Result').show();
            } else {
                $('#'+CHAT_FLAGS[i]).removeAttr('checked');
                $('#'+CHAT_FLAGS[i]+'Result').hide();
            }
        }

        if (typeof data.chat.topic!='undefined') {
            $('#topic').html(bbEncode(data.chat.topic));
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
        if (data.chat['nsfw'] == '1') {
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
        $('.opmod input').prop('disabled', 'disabled');
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
    $('input, select, button').prop('disabled', 'disabled');
    setSidebar(null);
    document.title = (chat.title || chat.url)+' – '+ORIGINAL_TITLE;
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

    // if the sidebar changed, check bottom and go to bottom if at bottom
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
        while (c.charAt(0)==' ') c = c.substr(1,c.length);
        if (c.indexOf(nameEQ) == 0) return c.substr(nameEQ.length,c.length);
    }
    return null;
}

function updateChatPreview(){
    $('#aliasOffset').css('top', (5-$('#textInput').scrollTop())+px);
    var at_bottom = atBottom(CONVERSATION_CONTAINER);
    var textPreview = $('#textInput').val().replace(/\r\n|\r|\n/g,"[br]");
    $('#textInput').css('opacity','1');
    $('#aliasOffset').css('opacity','1');
    $('#preview').css('opacity','1');
    $('#preview').css('color', '#'+user.character.color);
    $('#textInput').css('color', '#'+user.character.color);
    $('#aliasOffset').css('color', '#'+user.character.color);
    $('#aliasOffset').text(user.character.acronym+":").css('color','#'+user.character.color);
    $("#textInput").css('text-indent', ($('#aliasOffset').width()+4)+"px");
    
    var command = $('#textInput').val().split(' ');
    
    if (command[0] == '/ic' || command[0] == '/ooc' ||
            command[0] == '/ban' || command[0] == '/kick' ||
            command[0] == '/set' || command[0] == '/topic' ||
            command[0] == '/publicity' || command[0] == '/ns