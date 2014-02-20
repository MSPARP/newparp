$(document).ready(function() {
    $('.stats a.tag').on('click', function(e){
        if ($('textarea.tags').val()) {
            $('textarea.tags').val($('textarea.tags').val()+', '+$(this).text());
        } else {
            $('textarea.tags').val($(this).text());
        }
        e.preventDefault();
    });

    $("#nsfwsfw").change(function(){
        if ($(this).children(":selected").val() == 1) {
            //NSFW
        } else {
            //SFW
        }
    });

    jQuery.expr[':'].focus = function( elem ) {
      return elem === document.activeElement && ( elem.type || elem.href );
    };

    $('#frontform').submit(function() {
        if ($("#groupsub, #modpass").is(":focus")) {
            $('#frontform').append('<input type="hidden" name="create" value="Create Chat Room">');
        }
    });

    if (document.cookie=="") {
        $('<p class="error">').text("It seems you have cookies disabled. Unfortunately cookies are essential for MSPARP to work, so you'll need to either enable them or add an exception in order to use MSPARP.").appendTo(document.body);
    }

    var settingUp = true;
    var config = $('#character-config');

    function updatePreview() {
        $('#color-preview').css('color', '#'+config.find('input[name="color"]').val());
        var acronym = config.find('input[name="acronym"]').val();
        $('#color-preview #acronym').text(acronym+(acronym.length>0?': ':''));
    }
    config.find('input').change(updatePreview).keyup(updatePreview);
    updatePreview();

    $('input[name="picky"]').change(function() {
        if($(this).is(':checked')) {
            $('#picky-matches').show();
        } else {
            $('#picky-matches').hide();
            $('#picky-matches input').removeAttr('checked').removeAttr('indeterminate');
        }
    }).change();

    $('label.picky-header input').click(function() {
        var checks = $(this.parentNode).next('div.picky-group').find('input');
        if (this.checked) {
            checks.attr('checked','checked');
        } else {
            checks.val([]);
        }
    });

    function setGroupInput(groupDiv) {
        var label = $(groupDiv).prev('label.picky-header').find('input')[0];
        var group = $(groupDiv).find('input');
        var groupChecked = $(groupDiv).find('input:checked');
        if (groupChecked.length==0) {
            $(label).removeAttr('checked').removeAttr('indeterminate');
        } else if (groupChecked.length==group.length) {
            $(label).removeAttr('indeterminate').attr('checked','checked');
        } else {
            $(label).removeAttr('checked').attr('indeterminate','indeterminate');
        }
    }

    var pickyGroups = $('div.picky-group');
    for (i=0; i<pickyGroups.length; i++) {
        setGroupInput(pickyGroups[i]);
    }

    $('div.picky-group input').click(function() {
        setGroupInput(this.parentNode.parentNode);
    });

    $('div.defaults-off').hide();
    settingUp=false;

});
