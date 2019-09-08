function restart() {
    $.ajax({
        type: "GET",
        url: "{{ url_for('restart_song') }}",
        async: true
    });
}

function playpause() {
    $.ajax({
        type: "GET",
        url: "{{ url_for('play_pause') }}",
        async: true
    });
}

function fullscreen() {
    $.ajax({
        type: "GET",
        url: "{{ url_for('fullscreen') }}",
        async: true
    });
}

function skip() {
    $.ajax({
        type: "GET",
        url: "{{ url_for('skip_song') }}",
        async: true
    });
}

function recommend() {
    $.ajax({
        type: "GET",
        url: "{{ url_for('recommend') }}",
        async: true
    });
}

function findsongs() {
    $.ajax({
        type: "GET",
        url: "{{ url_for('get_folder') }}",
        async: true
    });
}

function toggle_admin(username) {
    $.ajax({
        type: "GET",
        url: "{{ url_for('toggle_admin') }}",
        data: {
            'username':username
        },
        async: true
    });
}

function set_singer_idx() {
    var idx = document.getElementById('singer_idx').value;

    $.ajax({
        type: "GET",
        data: { 'idx': idx },
        url: "{{ url_for('set_singer_idx') }}",
        async: true
    });
}

function manual_queue() {
    var title = document.getElementById('title').value; 
    var song_id = document.getElementById('song_id').value; 

    do_queue_song("", title, song_id, "youtube");
}

function query() {
    var search_term = document.getElementById('search_query').value; 
    console.log("Search term:" + search_term);
    //alert("From was submitted:" + search_term);
    $.ajax({
        type: "GET",
        url: "{{ url_for('search_local') }}",
        data: {'term':search_term},
        async: true,
        success: function(data) {
            //console.log("Local return: " + data);
            localStorage.setItem('local_results', data);
            $('#data_loc').html(data);
        }
    });
    $.ajax({
        type: "GET",
        url: "{{ url_for('search_web') }}",
        data: {'term':search_term},
        async: true,
        success: function(data) {
            //console.log("Web return: " + data);
            localStorage.setItem('web_results', data);
            $('#data_web').html(data);
        }
    });
    //server.do_local_query(search_term, onLocalReturn); 
    //server.do_web_query(search_term, onWebReturn); 
}

function set_favorite(artist, title, path, archive, duration) {
    $.ajax({
        type: "GET",
        url: "{{ url_for('set_favorite') }}",
        data: {
            'artist':artist,
            'title':title,
            'path':path,
            'archive':archive,
            'duration':duration
        },
        async: true,
        success: function(data) {
			close_dialog();
            recommend();
        }
    });
}

function drop_favorite(artist, title, path, archive, duration) {
    $.ajax({
        type: "GET",
        url: "{{ url_for('drop_favorite') }}",
        data: {
            'artist':artist,
            'title':title,
            'path':path,
            'archive':archive,
            'duration':duration
        },
        async: true,
        success: function(data) {
			close_dialog();
            recommend();
        }
    });
}


function do_click_song(artist, title, path, archive, duration, state) {
    $.ajax({
        type: "GET",
        url: "{{ url_for('song_dialog') }}",
        data: {
            'artist':artist,
            'title':title,
            'path':path,
            'archive':archive,
            'duration':duration,
			'state':state
        },
        async: true,
        success: function(data) {
            $('#dialog').html(data);
            $('#dialog').css("display", "block");
        }
    });
}

function close_dialog() {
	$('#dialog').css("display", "none");
}

function do_queue_song(artist, title, path, archive, duration) {
/*    var ret = confirm("Add "+artist+" "+title+" to queue?");
    if ( ret != true) {
        return;
    }
*/
    $.ajax({
        type: "GET",
        url: "{{ url_for('queue_song') }}",
        data: {
            'artist':artist,
            'title':title,
            'path':path,
            'archive':archive,
            'duration':duration
        },
        async: true,
        success: function(data) {
            console.log("Queueing song success: " + data);
            $('#user_data').html("You chose " + unescape(title) + " next!");
			close_dialog();
        }
    });
   
}

function do_unqueue_song(artist, title, path, archive, idx) {
    $.ajax({
        type: "GET",
        url: "{{ url_for('unqueue_song') }}",
        data: {
            'path':path,
            'idx':idx
        },
        async: true,
        success: function(data) {
            console.log("Un-Queueing song success: " + data);
            //$('#user_data').html("You chose " + unescape(title) + " next!");
        }

    });
}


function do_queue_up(idx) {
    $.ajax({
        type: "GET",
        url: "{{ url_for('queue_up') }}",
        data: {
            'idx':idx
        },
        async: true,
        success: function(data) {
            console.log("Queue up song success: " + data);
        }
    });
}

function do_queue_down(idx) {
    $.ajax({
        type: "GET",
        url: "{{ url_for('queue_down') }}",
        data: {
            'idx':idx
        },
        async: true,
        success: function(data) {
            console.log("Queue down song success: " + data);
        }
    });
}

function search() {
	//var $rows = $('#song_table tr');
	var $rows = $('.collapsed');

	var val = '^(?=.*\\b' + $.trim($('#song_search').val()).split(/\s+/).join('\\b)(?=.*\\b') + ').*$',
		reg = RegExp(val, 'i'),
		text;

    $.ajax({
        type: "GET",
        url: "{{ url_for('search_web') }}",
        data: {'term':$('#song_search').val()},
        async: true,
        success: function(data) {
            //console.log("Web return: " + data);
            localStorage.setItem('web_results', data);
            $('#data_web').html(data);
        }
    });

    var firstmatch = true;
    /*
    $rows.filter(function(){
		text = $(this).text().replace(/\s+/g, ' ');
        
        if(reg.test(text)) {
            if($(this_row).attr('expand') 
        }

    }).toggle();
    */
	$rows.filter(function() {
		text = $(this).text().replace(/\s+/g, ' ');
		//return !reg.test(text);
	    if(reg.test(text)) {
            // We matched

            if(firstmatch) {
                $(this).get(0).scrollIntoView();
                firstmatch = false;
            }

            if($(this).is(":hidden")){
                // Hidden, so toggle
                return true
            }
        } else if (! $(this).is(":hidden")){
            // Not hidden and a miss so toggle
            return true
        }
        else {
            return false
        }
	}).toggle();
}

function expand_collapse(this_row, idx) {
	var $rows = $('.row_'+idx);
    console.log(this_row);
    var expanded = $(this_row).attr('expand');
    console.log(expanded);
    //var text;
    //var reg = RegExp('^'+idx+'.*$', 'i');
    //console.log(reg);

    /*$rows.show().filter(function() {
		text = $(this).text().replace(/\s+/g, ' ');
        console.log(text);
		return !reg.test(text);
	}).hide();
    */

    $rows.show().filter(function() {
        if(this.getAttribute('idx') == idx) {
            // Found match
            if(expanded == 1) {
                // Expanded already, so hide it
                return true;
            } else {
                // Not expanded, so show it
                return false;
            }
        } else {
            // No match, so hide
            return true;
        }
    }).hide();

    if(expanded == 1) {
        $(this_row).attr('expand', 0);
    } else {
        $(this_row).attr('expand', 1);
    }
}

function hide_rows() {
	var $rows = $('.collapsed');
    $rows.css('display', 'table-row');
    $rows.hide();

    /*
    var coll = document.getElementsByClassName("collapsible");
    var conn = document.getElementsByClassName("collapsed");
    var i;
    var j;
    for (i = 0; i < coll.length; i++) {
        coll[i].addEventListener("click", function() {
            this.classList.toggle("active");
            console.log(this);
            console.log(this.getAttribute('idx'));
            var matchfound = false;

            for (j=0; j < conn.length; j++) {
                elem = conn[j];
                console.log(elem);
                console.log(elem.getAttribute('idx'));
                
                if(this.getAttribute('idx') == elem.getAttribute('idx')) {
                    matchfound = true;
                    if (elem.style.display === "block") {
                        elem.style.display = "none";
                    } else {
                        elem.style.display = "block";
                    }
                } else if (matchfound) {
                    break;
                }
            }
        });
    }*/
}
