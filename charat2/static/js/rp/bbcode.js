function linkify(inputText) {
    var replacedText, replacePattern1, replacePattern2;

    //URLs starting with http://, https://, or ftp://
    replacePattern1 = /]?=?https?:\/\/[-a-zA-Z0-9@:%._\+~#=]{2,256}\.[a-z]{2,6}\b([-a-zA-Z0-9@:%_\+.~#?&//=]*)/gim;
    replacedText = inputText.replace(replacePattern1,
    function(m) {
        if (m.substr(0,1) == "=" || m.substr(0,1) == "]") {
            return m;
        } else {
            return "[url]"+m+"[/url]";
        }
    });

    //Change email addresses to mailto:: links.
    replacePattern2 = /(\w+@[a-zA-Z_]+?\.[a-zA-Z]{2,6})/gim;
    replacedText = replacedText.replace(replacePattern2, '[email]$1[/email]');

    return replacedText;
}

function bbEncode(S) {
    S = linkify($('<div/>').text(S).html());
    if (S.indexOf('[') < 0 || S.indexOf(']') < 0) return S;
    
    S = S.replace(/\[(font|color|bgcolor|tshadow|bshadow)=([^\]]+)]/gi, function(one,two,three) {
        three = three.replace(/["';{}]/gi, "");
        return "["+two+"="+three+"]";
    });

    var BR = true;
    while (BR == true) {
        BR = false;
        S = S.replace(/\[br]\s?\[br]/gi, function(w) {
            if (w) { BR = true; }
            return '[br]';
        });
    }

    function X(p, f) {return new RegExp(p, f)}
    function D(s) {return rD.exec(s)}
    function R(s) {return s.replace(rB, P);}
    function A(s, p) {for (var i in p) s = s.replace(X(i, 'g'), p[i]); return s;}

    function P($0, $1, $2, $3) {
        if ($3 && $3.indexOf('[') > -1) $3 = R($3);
        var linkint = ($2||$3).trim();
        if (linkint.substr(0,11) == "javascript:") { linkint = linkint.substring(11); }
        if (linkint.substr(0,12) == "javascript :") { linkint = linkint.substring(12); }
        linkint = linkint.replace(/["';{}]/g, "");
        $2 = linkint;
        switch ($1) {
            case 'url':case 'email': return '<a target="_blank" '+ L[$1] + $2 +'">'+ $3 +'</a>';
            case 'pad': return '<span class="padded">'+ $3 +'</span>';
            case 'spoiler': return '<span class="spoil"><span class="spoiler">'+ $3 +'</span></span>';
            case 'b':case 'i':case 'u':case 's':case 'sup':case 'sub': return '<'+ $1 +'>'+ $3 +'</'+ $1 +'>';
        }
        return '['+ $1 + ']'+ $3 +'[/'+ $1 +']';
    }

    var C = {code: [{'\\[': '&#91;', ']': '&#93;'}, '', '']};
    var rB = X('\\[([a-z][a-z0-9]*)(?:=([^\\]]+))?]((?:.|[\r\n])*?)\\[/\\1]', 'g'), rD = X('^(\\d+)x(\\d+)$');
    var L = {url: 'href="', email: 'href="mailto: '};
    var F = {font: 'font-family:$1', color: 'color:$1', bgcolor: 'background-color:$1', tshadow: 'line-height:20px;text-shadow:$1', bshadow: 'line-height:20px;box-shadow:$1'};
    var I = {}, B = {};

    for (var i in C) I['\\[('+ i +')]((?:.|[\r\n])*?)\\[/\\1]'] = function($0, $1, $2) {return C[$1][1] + A($2, C[$1][0]) + C[$1][2]};
    for (var i in F) {B['\\['+ i +'=([^\\]]+)]'] = '<span style="'+ F[i] +'">'; B['\\[/'+ i +']'] = '</span>';}
    B['\\[(br)]'] = '<$1 />';

    var result = R(A(A(S, I), B));
    return result;
}

function bbRemove(S) {
    if (S.indexOf('[') < 0 || S.indexOf(']') < 0) return S;

    function X(p, f) {return new RegExp(p, f)}
    function D(s) {return rD.exec(s)}
    function R(s) {return s.replace(rB, P)}
    function A(s, p) {for (var i in p) s = s.replace(X(i, 'g'), p[i]); return s;}

    function P($0, $1, $2, $3) {
        if ($3 && $3.indexOf('[') > -1) $3 = R($3);
        switch ($1) {
            case 'pad': return '$3';
        }
        return '['+ $1 + ']'+ $3 +'[/'+ $1 +']';
    }

    var rB = X('\\[([a-z][a-z0-9]*)(?:=([^\\]]+))?]((?:.|[\r\n])*?)\\[/\\1]', 'g'), rD = X('^(\\d+)x(\\d+)$');
    var F = {font: 'font-family:$1', color: 'color:$1', bgcolor: 'background-color:$1', tshadow: 'text-shadow:$1', bshadow: 'box-shadow:$1'};
    var I = {}, B = {};

    for (var i in F) {B['\\['+ i +'=([^\\]]+)]'] = ''; B['\\[/'+ i +']'] = '';}
    var result = R(A(A(S, I), B));
    return result;
}

function bbRemoveAll(S) {
    S = linkify($('<div/>').text(S).html());
    if (S.indexOf('[') < 0 || S.indexOf(']') < 0) return S;

    function X(p, f) {return new RegExp(p, f)}
    function D(s) {return rD.exec(s)}
    function R(s) {return s.replace(rB, P);}
    function A(s, p) {for (var i in p) s = s.replace(X(i, 'g'), p[i]); return s;}

    function P($0, $1, $2, $3) {
        if ($3 && $3.indexOf('[') > -1) $3 = R($3);
        var linkint = ($2||$3).trim();
        if (linkint.substr(0,11) == "javascript:") { linkint = linkint.substring(11); }
        if (linkint.substr(0,12) == "javascript :") { linkint = linkint.substring(12); }
        linkint = linkint.replace(/["';{}]/g, "");
        $2 = linkint;
        switch ($1) {
            case 'pad': return $3;
            case 'spoiler': return $3;
            case 'b':case 'i':case 'u':case 's':case 'sup':case 'sub': return $3;
        }
        return '['+ $1 + ']'+ $3 +'[/'+ $1 +']';
    }

    var C = {code: [{'\\[': '&#91;', ']': '&#93;'}, '', '']};
    var rB = X('\\[([a-z][a-z0-9]*)(?:=([^\\]]+))?]((?:.|[\r\n])*?)\\[/\\1]', 'g'), rD = X('^(\\d+)x(\\d+)$');
    var F = {font: 'font-family:$1', color: 'color:$1', bgcolor: 'background-color:$1', tshadow: 'line-height:20px;text-shadow:$1', bshadow: 'line-height:20px;box-shadow:$1'};
    var I = {}, B = {};

    for (var i in C) I['\\[('+ i +')]((?:.|[\r\n])*?)\\[/\\1]'] = function($0, $1, $2) {return C[$1][1] + A($2, C[$1][0]) + C[$1][2]};
    for (var i in F) {B['\\['+ i +'=([^\\]]+)]'] = ''; B['\\[/'+ i +']'] = '';}
    B['\\[(br)]'] = '';

    var result = R(A(A(S, I), B));
    return result;
}

$(document).ready(function(){
    $(document.body).on('click', '.spoiler', function() {
        if ($(this).css('opacity') == '0') {
            $(this).css('opacity','1');
        } else {
            $(this).css('opacity','0');
        }
    });
});


