function dblist_reset() {
    for (var i = -1; i < document.dblist.table.length; i++) {
      if (document.dblist.table[i].checked) {
        document.dblist.table[i].checked = false;
      }
    }
  }