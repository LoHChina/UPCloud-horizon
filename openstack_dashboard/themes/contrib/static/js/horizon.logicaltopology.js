/* global Hogan */
/* Namespace for core functionality related to Logical Topology. */

function Database(data) {
  for (var key in data) {
    if ({}.hasOwnProperty.call(data, key)) {
      this[key] = data[key];
    }
  }
  this.iconType = 'text';
  this.icon = '\uf1c0'; // Database
  this.collapsed = false;
  this.type = 'database';
}

function MQ(data) {
  for (var key in data) {
    if ({}.hasOwnProperty.call(data, key)) {
      this[key] = data[key];
    }
  }
  this.iconType = 'text';
  this.icon = '\uf0ec'; // MQ
  this.collapsed = false;
  this.type = 'mq';
}

function Computer(data) {
  for (var key in data) {
    if ({}.hasOwnProperty.call(data, key)) {
      this[key] = data[key];
    }
  }
  this.iconType = 'text';
  this.icon = '\uf233'; // Computer
  this.collapsed = false;
  this.type = 'computer';
}

function Haproxy(data) {
  for (var key in data) {
    if ({}.hasOwnProperty.call(data, key)) {
      this[key] = data[key];
    }
  }
  this.iconType = 'text';
  this.icon = '\uf074'; // Haproxy
  this.collapsed = false;
  this.type = 'haproxy';
}

function Keystone(data) {
  for (var key in data) {
    if ({}.hasOwnProperty.call(data, key)) {
      this[key] = data[key];
    }
  }
  this.iconType = 'text';
  this.icon = '\uf007'; // Keystone
  this.collapsed = false;
  this.type = 'keystone';
}

horizon.logical_topology = {
  svg:'#logical_topology_canvas',
  nodes: [],
  links: [],
  data: [],
  zoom: d3.behavior.zoom(),
  data_loaded: false,
  svg_container:'#logicaltopologyCanvasContainer',
  post_messages:'#logicaltopologyMessages',
  reload_duration: 10000000,
  previous_message : null,

  init:function() {
    var self = this;
    angular.element(self.svg_container).spin(horizon.conf.spinner_options.modal);

    self.data = {};
    self.data.databases = {};
    self.data.mqs = {};
    self.data.haproxys = {};
    self.data.keystones = {};
    self.data.computers = {};
    self.data.links = {};

    angular.element('#toggle_labels').click(function() {
      if (angular.element('.nodeLabel').css('display') == 'none') {
        angular.element('.nodeLabel').show();
        horizon.cookies.put('show_labels', true);
      } else {
        angular.element('.nodeLabel').hide();
        horizon.cookies.put('show_labels', false);
      }
    });

    angular.element('#toggle_networks').click(function() {
      var _proxy = []
      for (var n in self.nodes) {
        if (self.nodes[n].data instanceof Haproxy) {
          _proxy.push(self.nodes[n])
        }
      }
      console.log(_proxy)

      for (_i in _proxy) {
        self.collapse_topology(_proxy[_i]);
      }

      if (horizon.cookies.get('show_labels')) {
        angular.element('.nodeLabel').show();
      }

      var current = horizon.cookies.get('are_networks_collapsed');
      horizon.cookies.put('are_networks_collapsed', !current);

    });

    angular.element(self.svg_container).spin(horizon.conf.spinner_options.modal);
    self.create_vis();
    self.loading();
    self.force_direction(0.08,70,-700);
    self.retrieve_info(true);
  },

  retrieve_info: function(force_start) {
    var self = this;
    angular.element.getJSON(
      angular.element('#logicaltopology').data('logicaltopology') + '?' + angular.element.now(),
      function(data) {
        self.data_loaded = true;
        self.load_topology(data);
        if (force_start) {
          var i = 0;
          self.force.start();
          while (i <= 100) {
            self.force.tick();
            i++;
          }
        }
        setTimeout(function() {
          self.retrieve_info();
        }, self.reload_duration);
      }
    );
  },

  load_config: function() {
    var labels = horizon.cookies.get('show_labels');
    var networks = horizon.cookies.get('are_networks_collapsed');
    if (labels) {
      angular.element('.nodeLabel').show();
      angular.element('#toggle_labels').addClass('active');
    }
    if (networks) {
      var _proxy = []
      for (var n in this.nodes) {
        if (this.nodes[n].data instanceof Haproxy) {
          _proxy.push(this.nodes[n])
        }
      }

      for (_i in _proxy) {
        this.collapse_topology(_proxy[_i], true);
      }

      angular.element('#toggle_networks').addClass('active');
    }
  },

  getScreenCoords: function(x, y) {
    var self = this;
    if (self.translate) {
      var xn = self.translate[0] + x * self.zoom.scale();
      var yn = self.translate[1] + y * self.zoom.scale();
      return { x: xn, y: yn };
    } else {
      return { x: x, y: y };
    }
  },

  create_vis: function() {
    var self = this;
    angular.element(self.svg_container).html('');

    self.outer_group = d3.select(self.svg_container).append('svg')
      .attr('width', '100%')
      .attr('height', angular.element(document).height() - 200 + "px")
      .attr('pointer-events', 'all')
      .append('g')
      .call(self.zoom
        .scaleExtent([0.1,1.5])
        .on('zoom', function() {
            self.vis.attr('transform', 'translate(' + d3.event.translate + ')scale(' +
              self.zoom.scale() + ')');
            self.translate = d3.event.translate;
          })
        )
      .on('dblclick.zoom', null);

    self.outer_group.append('rect')
      .attr('width', '100%')
      .attr('height', '100%')
      .attr('fill', 'white')
      .on('click', function(d) {
      });

    self.vis = self.outer_group.append('g');
  },

  loading: function() {
    var self = this;
    var load_text = self.vis.append('text')
        .style('fill', 'black')
        .style('font-size', '40')
        .attr('x', '50%')
        .attr('y', '50%')
        .text('');
    var counter = 0;
    var timer = setInterval(function() {
      var i;
      var str = '';
      for (i = 0; i <= counter; i++) {
        str += '.';
      }
      load_text.text(str);
      if (counter >= 9) {
        counter = 0;
      } else {
        counter++;
      }
      if (self.data_loaded) {
        clearInterval(timer);
        load_text.remove();
      }
    }, 100);
  },

  convex_hulls: function(nodes) {
    var object, _i, _len, _ref, _h, i;
    var hulls = {};
    var controllers = {};
    var k = 0;
    var offset = 40;

    while ( k < nodes.length) {
      var n = nodes[k];
      if (n.data !== undefined) {
          object = n.data;
          controllers[object.phycical_node] = n;
          _h = hulls[object.phycical_node] || (hulls[object.phycical_node] = []);
          _h.push([n.x - offset, n.y - offset]);
          _h.push([n.x - offset, n.y + offset]);
          _h.push([n.x + offset, n.y - offset]);
          _h.push([n.x + offset, n.y + offset]);
      }
      ++k;
    }
    var hullset = [];
    for (i in hulls) {
      if ({}.hasOwnProperty.call(hulls, i)) {
        hullset.push({group: i, controller: controllers[i], path: d3.geom.hull(hulls[i])});
      }
    }

    return hullset;
  },

  force_direction: function(grav, dist, ch) {
    var self = this;

    angular.element('[data-toggle="tooltip"]').tooltip({container: 'body'});
    self.curve = d3.svg.line()
      .interpolate('cardinal-closed')
      .tension(0.85);
    self.fill = d3.scale.category10();

    self.force = d3.layout.force()
      .gravity(grav)
      .linkDistance(function(d) {
        if (d.source.data instanceof Computer) {
          return dist + 120;
        } else {
          return dist + 20;
        }
      })
      .charge(ch)
      .size([angular.element(self.svg_container).width(),
             angular.element(self.svg_container).height()])
      .nodes(self.nodes)
      .links(self.links)
      .on('tick', function() {
        self.vis.selectAll('g.node')
          .attr('transform', function(d) {
            return 'translate(' + d.x + ',' + d.y + ')';
          });

        self.vis.selectAll('line.link')
          .attr('x1', function(d) { return d.source.x; })
          .attr('y1', function(d) { return d.source.y; })
          .attr('x2', function(d) { return d.target.x; })
          .attr('y2', function(d) { return d.target.y; });

        self.vis.selectAll('path.hulls')
          .data(self.convex_hulls(self.vis.selectAll('g.node').data()))
            .attr('d', function(d) {
              return self.curve(d.path);
            })
          .enter().insert('path', 'g')
            .attr('class', 'hulls')
            .style('fill', function(d) {
              return self.fill(d.group);
            })
            .style('stroke', function(d) {
              return self.fill(d.group);
            })
            .style('stroke-linejoin', 'round')
            .style('stroke-width', 10)
            .style('opacity', 0.2);
      });
  },

  new_node: function(data, x, y) {
    var self = this;
    data = {data: data};
    if (x && y) {
      data.x = x;
      data.y = y;
    }
    self.nodes.push(data);

    var node = self.vis.selectAll('g.node').data(self.nodes);
    var nodeEnter = node.enter().append('g')
      .attr('class', 'node')
      .style('fill', 'white')
      .call(self.force.drag);

    nodeEnter.append('circle')
      .attr('class', 'frame')
      .attr('r', function(d) {
        return 30;
      })
      .style('fill', 'white')
      .style('stroke', 'black')
      .style('stroke-width', 3);

    switch ( data.data.iconType ) {
      case 'text':
        nodeEnter.append('text')
          .style('fill', 'black')
          .style('font', '20px FontAwesome')
          .attr('text-anchor', 'middle')
          .attr('dominant-baseline', 'central')
          .text(function(d) { return d.data.icon; })
          .attr('transform', function(d) {
              return 'scale(1)';
          });
        break;
      case 'path':
        nodeEnter.append('path')
          .attr('class', 'svgpath')
          .style('fill', 'black')
          .attr('d', function(d) { return self.svgs(d.data.svg); })
          .attr('transform', function() {
            return 'scale(1.2)translate(-16,-15)';
          });
        break;
    }

    nodeEnter.append('text')
      .attr('class', 'nodeLabel')
      .style('display',function() {
        var labels = horizon.cookies.get('topology_labels');
        if (labels) {
          return 'inline';
        } else {
          return 'none';
        }
      })
      .style('fill','black')
      .text(function(d) {
        return d.data.name;
      })
      .attr('transform', function(d) {
          return 'translate(35,3)';
      });

    if (data.data instanceof Haproxy) {
      nodeEnter.append('svg:text')
        .attr('class','controller')
        .style('fill', 'black')
        .style('font-size','20')
        .text('')
        .attr('transform', 'translate(26,38)');
    }

    nodeEnter.on('click', function(d) {
      self.show_balloon(d.data, d, angular.element(this));
    });

    nodeEnter.on('mouseover', function(d) {
      self.vis.selectAll('line.link').filter(function(z) {
        if (z.source === d || z.target === d) {
          return true;
        } else {
          return false;
        }
      }).style('stroke-width', '3px');
    });

    nodeEnter.on('mouseout', function() {
      self.vis.selectAll('line.link').style('stroke-width','1px');
    });
  },

  collapse_topology: function(d, only_collapse) {
    var self = this;

    var filterNode = function(obj) {
      return function(d) {
        return obj == d.data;
      };
    };

    if (!d.data.collapsed) {
      for (db in self.data.databases) {
        if (self.data.databases[db] !== undefined) {
          if (self.data.databases[db].haproxy == d.data.id) {
            self.removeNode(self.data.databases[db]);
          }
        }
      }

      for (mq in self.data.mqs) {
        if (self.data.mqs[mq] !== undefined) {
          if (self.data.mqs[mq].haproxy == d.data.id) {
            self.removeNode(self.data.mqs[mq]);
          }
        }
      }

      for (key in self.data.keystones) {
        if (self.data.keystones[key] !== undefined) {
          if (self.data.keystones[key].haproxy == d.data.id) {
            self.removeNode(self.data.keystones[key]);
          }
        }
      }
      d.data.collapsed = true;
      //if (vmCount > 0) {
      //  self.vis.selectAll('.vmCount').filter(filterNode(d.data))[0][0].textContent = vmCount;
      //}
    } else if (!only_collapse) {
      for (db in self.data.databases) {
        if ({}.hasOwnProperty.call(self.data.databases, db)) {
          var _db = self.data.databases[db];
          if (_db !== undefined) {
            if (_db.haproxy == d.data.id) {
              self.new_node(_db, d.x, d.y);
              self.new_link(self.find_by_id(_db.id), self.find_by_id(d.data.id));
              self.force.start();
            }
          }
        }
      }

      for (mq in self.data.mqs) {
        if ({}.hasOwnProperty.call(self.data.mqs, mq)) {
          var _mq = self.data.mqs[mq];
          if (_mq !== undefined) {
            if (_mq.haproxy == d.data.id) {
              self.new_node(_mq, d.x, d.y);
              self.new_link(self.find_by_id(_mq.id), self.find_by_id(d.data.id));
              self.force.start();
            }
          }
        }
      }

      for (key in self.data.keystones) {
        if ({}.hasOwnProperty.call(self.data.keystones, key)) {
          var _key = self.data.keystones[key];
          if (_key !== undefined) {
            if (_key.haproxy == d.data.id) {
              self.new_node(_key, d.x, d.y);
              self.new_link(self.find_by_id(_key.id), self.find_by_id(d.data.id));
              self.force.start();
            }
          }
        }
      }

      d.data.collapsed = false;
      //self.vis.selectAll('.vmCount').filter(filterNode(d.data))[0][0].textContent = '';
      var i = 0;
      while (i <= 100) {
        self.force.tick();
        i++;
      }
    }
  },

  new_link: function(source, target) {
    var self = this;
    self.links.push({source: source, target: target});
    var line = self.vis.selectAll('line.link').data(self.links);
    line.enter().insert('line', 'g.node')
      .attr('class', 'link')
      .attr('x1', function(d) { return d.source.x; })
      .attr('y1', function(d) { return d.source.y; })
      .attr('x2', function(d) { return d.target.x; })
      .attr('y2', function(d) { return d.target.y; })
      .style('stroke', 'black')
      .style('stroke-width', 2);
  },

  find_by_id: function(id) {
    var self = this;
    var obj, _i, _len, _ref;
    _ref = self.vis.selectAll('g.node').data();
    for (_i = 0, _len = _ref.length; _i < _len; _i++) {
      obj = _ref[_i];
      if (obj.data.id == id) {
        return obj;
      }
    }
    return undefined;
  },

  already_in_graph: function(data, node) {
    for (var n in data) {
      if (n == node.id) {
        return true;
      }
    }
    return false;
  },

  load_topology: function(data) {
    var self = this;
    var db, _dblen, _dbref,
        mq, _mqlen, _mqref,
        com, _comlen, _comref,
        key, _keylen, _keyref,
        proxy, _proxylen, _proxyref,
        link, _linklen, _linkref,
        obj, _i;
    var change = false;
    var filterNode = function(obj) {
      return function(d) {
        return obj == d.data;
      };
    };

    // Database
    _dbref = data.databases;
    for (_i = 0, _dblen = _dbref.length; _i < _dblen; _i++) {
      db = _dbref[_i];
      var database = new Database(db);

      if (!self.already_in_graph(self.data.databases, database)) {
        self.new_node(database);
        change = true;
      } else {
        obj = self.find_by_id(database.id);
        if (obj) {
          obj.data = database;
        }
      }
      self.data.databases[database.id] = database;
    }

    // MQ
    _mqref = data.mqs;
    for (_i = 0, _mqlen = _mqref.length; _i < _mqlen; _i++) {
      mq = _mqref[_i];
      var message_queue = new MQ(mq);

      if (!self.already_in_graph(self.data.mqs, message_queue)) {
        self.new_node(message_queue);
        change = true;
      } else {
        obj = self.find_by_id(message_queue.id);
        if (obj) {
          obj.data = message_queue;
        }
      }
      self.data.mqs[message_queue.id] = message_queue;
    }

    // Computer
    _comref = data.computers;
    for (_i = 0, _comlen = _comref.length; _i < _comlen; _i++) {
      com = _comref[_i];
      var computer = new Computer(com);

      if (!self.already_in_graph(self.data.computers, computer)) {
        self.new_node(computer);
        change = true;
      } else {
        obj = self.find_by_id(computer.id);
        if (obj) {
          obj.data = computer;
        }
      }
      self.data.computers[computer.id] = computer;
    }

    // Haproxy
    _proxyref = data.haproxys;
    for (_i = 0, _proxylen = _proxyref.length; _i < _proxylen; _i++) {
      proxy = _proxyref[_i];
      var haproxy = new Haproxy(proxy);

      if (!self.already_in_graph(self.data.haproxys, haproxy)) {
        self.new_node(haproxy);
        change = true;
      } else {
        obj = self.find_by_id(haproxy.id);
        if (obj) {
          obj.data = haproxy;
        }
      }
      self.data.haproxys[haproxy.id] = haproxy;
    }

    // Keystone
    _keyref = data.keystones;
    for (_i = 0, _keylen = _keyref.length; _i < _keylen; _i++) {
      key = _keyref[_i];
      var keystone = new Keystone(key);

      if (!self.already_in_graph(self.data.keystones, keystone)) {
        self.new_node(keystone);
        change = true;
      } else {
        obj = self.find_by_id(keystone.id);
        if (obj) {
          obj.data = keystone;
        }
      }
      self.data.keystones[keystone.id] = keystone;
    }

    // Add links
    _linkref = data.links;
    for (_i = 0, _linklen = _linkref.length; _i < _linklen; _i++) {
      link = _linkref[_i];

      if (!self.already_in_graph(self.data.links, link)) {
        self.new_link(self.find_by_id(link.source), self.find_by_id(link.target));
        change = true;
      }

      self.data.links[link.id] = link;
    }

    if (change) {
      self.force.start();
    }
    self.load_config();
  },

  removeNode: function(obj) {
    var filterNode, n, node, _i, _len, _ref;
    _ref = this.nodes;
    for (_i = 0, _len = _ref.length; _i < _len; _i++) {
      n = _ref[_i];
      if (n.data === obj) {
        node = n;
        break;
      }
    }
    if (node) {
      this.nodes.splice(this.nodes.indexOf(node), 1);
      filterNode = function(obj) {
        return function(d) {
          return obj === d.data;
        };
      };
      this.vis.selectAll('g.node').filter(filterNode(obj)).remove();
      return this.removeNodesLinks(obj);
    }
  },

  removeNodesLinks: function(node) {
    var l, linksToRemove, _i, _j, _len, _len1, _ref;
    linksToRemove = [];
    _ref = this.links;
    for (_i = 0, _len = _ref.length; _i < _len; _i++) {
      l = _ref[_i];
      if (l.source.data === node) {
        linksToRemove.push(l);
      } else if (l.target.data === node) {
        linksToRemove.push(l);
      }
    }
    for (_j = 0, _len1 = linksToRemove.length; _j < _len1; _j++) {
      l = linksToRemove[_j];
      this.removeLink(l);
    }
    return this.force.resume();
  },

  removeLink: function(link) {
    var i, index, l, _i, _len, _ref;
    index = -1;
    _ref = this.links;
    for (i = _i = 0, _len = _ref.length; _i < _len; i = ++_i) {
      l = _ref[i];
      if (l === link) {
        index = i;
        break;
      }
    }
    if (index !== -1) {
      this.links.splice(index, 1);
    }
    return this.vis.selectAll('line.link').data(this.links).exit().remove();
  },

}
