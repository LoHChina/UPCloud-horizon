// TODO(lsmola) write a proper doc for each attribute and method
horizon.d3_line_chart_resource = {
  LineChart: function(chart_class, html_element){
    var self = this;
    var jquery_element = $(html_element);

    self.chart_class = chart_class;
    self.html_element = html_element;

    self.url = jquery_element.data("url");
    self.url_parameters = jquery_element.data("url_parameters");

    self.data = []
    self.color = d3.scale.category20();

    self.load_settings = function(settings) {
       // TODO (lsmola) make settings work
       /* Settings will be obtained either from Json from server,
          or from init of the charts, server will have priority */
       self.settings = {};
       self.settings.renderer = 'line';
       self.settings.auto_size = true;
    }
    self.get_size = function(){
      /* The height will be determined by css or window size,
         I have to hide everything inside that could mess with
         the size, so it is fully determined by outer CSS. */
      $(self.html_element).css("height", "");
      $(self.html_element).css("width", "");
      var svg = $(self.html_element).find("svg");
      svg.hide();

      // Width an height of the chart will be taken from chart wrapper,
      // that can be styled by css.
      self.width = jquery_element.width();

      // Set either the minimal height defined by CSS.
      self.height = jquery_element.height();

      /* Setting new sizes. It is important when resizing a window.*/
      $(self.html_element).css("height", self.height);
      $(self.html_element).css("width", self.width);
      svg.show();
      svg.css("height", self.height);
      svg.css("width", self.width);
    }
    // Load initial settings.
    self.load_settings({});
    // Get correct size of chart and the wrapper.
    self.get_size();

    self.refresh = function (data, data_type){
      var self = this;
      jquery_element.html("");
      self.series = data.series;
      self.load_settings(data.settings);
      if (self.series[0].data <= 0) {
        $(self.html_element).html(gettext("No data available."));
      } else {
        var all_series_data = self.series[0].data;
        var last_series_data = all_series_data[all_series_data.length-1];
        self.render(data_type);
        var unit = self.series[0].unit;
        $('.' + self.series[0].class).html(self.format_num(last_series_data.y) + " " + unit)
      }
    };

    self.convert_to_local_time = function(date){
        var d = new Date(date + "+00:00");
        utc = d.getTime();
        return utc
    }

    self.format_num = function(y) {
        var abs_y = Math.abs(y);
        if (abs_y >= 1000000000000)   { return (y / 1000000000000).toFixed(2) + "T" }
        else if (abs_y >= 1000000000) { return (y / 1000000000).toFixed(2) + "G" }
        else if (abs_y >= 1000000)    { return (y / 1000000).toFixed(2) + "M" }
        else if (abs_y >= 1000)       { return (y / 1000).toFixed(2) + "K" }
        else if (abs_y < 1000 && y >= 0)  { return y }
        else if (abs_y < 1 && y > 0)  { return y }
        else if (abs_y === 0)         { return '' }
        else                      { return y }
    };

    self.render = function(data_type){
      var self = this;

      $.map(self.series, function (serie) {
        $.map(serie.data, function (statistic) {
          statistic.x = d3.time.format.utc('%Y-%m-%dT%H:%M:%SZ').parse(statistic.x);
          statistic.x = statistic.x.getTime() / 1000;
        });
      });


      // instantiate our graph!
      var graph = new Rickshaw.Graph({
        element: self.html_element,
        width: self.width,
        height: self.height,
        renderer: self.settings.renderer,
        series: self.series,
        interpolation: 'linear',
      });

     var legend = document.querySelector('.resource_metric' + '_' + data_type);
     var legend = new Rickshaw.Graph.Legend({
          graph: graph,
          element:  legend
        });

      var Hover = Rickshaw.Class.create(Rickshaw.Graph.HoverDetail, {
          initialize: function(args) {
              var graph = this.graph = args.graph;

              this.xFormatter = args.xFormatter || function(x) {
                  var d = new Date(x * 1000);
                  var datetime_string = d.getFullYear() + "-" +
                      ("00" + (d.getMonth() + 1)).slice(-2) + "-" +
                      ("00" + d.getDate()).slice(-2) + " " +
                      ("00" + d.getHours()).slice(-2) + ":" +
                      ("00" + d.getMinutes()).slice(-2) + ":" +
                      ("00" + d.getUTCSeconds()).slice(-2);
                  return datetime_string;
              };

              this.yFormatter = args.yFormatter || function(y) {
                  return y === null ? y : y.toFixed(2);
              };

              var element = this.element = document.createElement('div');
              element.className = 'detail';

              this.visible = true;
              graph.element.appendChild(element);

              this.lastEvent = null;
              this._addListeners();

              this.onShow = args.onShow;
              this.onHide = args.onHide;
              this.onRender = args.onRender;

              this.formatter = args.formatter || this.formatter;

          },

          render: function(args) {

            if(args.points[0].formattedYValue) {
              var detail_container = document.createElement('div');
              detail_container.className = 'detail_container'
              this.element.appendChild(detail_container)
              this.element.classList.add("detail_border");
              var date_time = document.createElement('div');
              date_time.className = 'date_time'
              detail_container.appendChild(date_time)
              date_time.innerHTML = args.formattedXValue;

              args.detail.sort(function(a, b) { return a.order - b.order }).forEach( function(d) {

                  var line = document.createElement('div');
                  line.className = 'line';

                  var swatch = document.createElement('div');
                  swatch.className = 'detail_swatch';
                  swatch.style.backgroundColor = d.series.color;

                  var label = document.createElement('div');
                  label.className = 'label';
                  label.innerHTML = d.name + ": " + d.formattedYValue;

                  line.appendChild(swatch);
                  line.appendChild(label);

                  var dot = document.createElement('div');
                  dot.className = 'dot';
                  dot.style.top = graph.y(d.value.y0 + d.value.y) + 'px';
                  dot.style.borderColor = d.series.color;

                  detail_container.appendChild(line);
                  this.element.appendChild(dot);

                  dot.className = 'dot active';

                  this.show();
                  var alignables = [detail_container];
                  alignables.forEach(function(el) {
                      el.classList.add('hover_left');
                  });

                  var leftAlignError = this._calcLayoutError(alignables);
                  if (leftAlignError > 0) {
                      alignables.forEach(function(el) {
                          el.classList.remove('hover_left');
                          el.classList.add('hover_right');
                      });

                      var rightAlignError = this._calcLayoutError(alignables);
                      if (rightAlignError > leftAlignError) {
                          alignables.forEach(function(el) {
                              el.classList.remove('hover_right');
                              el.classList.add('hover_left');
                          });
                      }
                      }
              }, this );
            }
          }
      });

      var hover = new Hover( { graph: graph } );

      graph.render();

      var axes_x = new Rickshaw.Graph.Axis.Time({
        graph: graph,
        timeFixture: new Rickshaw.Fixtures.Time.Local(),
      });
      axes_x.render();

      var axes_y = new Rickshaw.Graph.Axis.Y({
        graph: graph,
        orientation: 'left',
        tickFormat: Rickshaw.Fixtures.Number.formatKMBT,
        ticks: 5,
        element: document.getElementById('y_axis' + '_' + data_type)
      });
      axes_y.render();

    };
  },
  init: function(selector, settings) {
    var self = this;
    self.send_ajax(selector, '?duration=5m&retention=6h');
    $("button.6h").click(function(){
      $('.btn-monitor button').removeClass('btn-primary');
      $(this).addClass('btn-primary');
      $('span.interval').html(gettext('5 Minutes'));
      self.send_ajax(selector, '?duration=5m&retention=6h');
    });
    $("button.1d").click(function(){
      $('.btn-monitor button').removeClass('btn-primary');
      $(this).addClass('btn-primary');
      $('span.interval').html(gettext('15 Minutes'));
      self.send_ajax(selector, '?duration=15m&retention=1d');
    });
    $("button.2w").click(function(){
      $('.btn-monitor button').removeClass('btn-primary');
      $(this).addClass('btn-primary');
      $('span.interval').html(gettext('2 Hours'));
      self.send_ajax(selector, '?duration=2h&retention=2w');
    });
    $("button.1m").click(function(){
      $('.btn-monitor button').removeClass('btn-primary');
      $(this).addClass('btn-primary');
      $('span.interval').html(gettext('1 Day'));
      self.send_ajax(selector, '?duration=1d&retention=4w');
    });
    $("button.6m").click(function(){
      $('.btn-monitor button').removeClass('btn-primary');
      $(this).addClass('btn-primary');
      $('span.interval').html(gettext('1 Day'));
      self.send_ajax(selector, '?duration=1d&retention=24w');
    });
  },
  send_ajax: function(selector, retention) {
    var self = this;
    var jquery_element = $(selector)
    self.final_url = jquery_element.data("url");
    self.final_url += retention
    if (jquery_element.data('form-selector')){
      $(jquery_element.data('form-selector')).each(function(){
        if (self.final_url.indexOf('?') > -1){
          self.final_url += '&' + $(this).serialize();
        } else {
          self.final_url += '?' + $(this).serialize();
        }
      });
    }

    // Retrieve the series 
    if (jquery_element.length) {
      jquery_element.empty();
      $('.y_axis').empty();
      $('.resource_metric').empty();
      jquery_element.spin(horizon.conf.spinner_options.inline);
      $.ajax({
        url: self.final_url,
        success: function (data, textStatus, jqXHR) {
          if ($.isEmptyObject(data)) {
            jquery_element.html(gettext("No data available."));
          } else {
            $(selector).each(function() {
              var data_type = $(this).data('type');
              var data_series = data[data_type]
              if (!$.isEmptyObject(data_series)) {
                self.refresh(this, data_series, data_type);
              }
            });
          }
        },
        error: function (jqXHR, textStatus, errorThrown) {
          jquery_element.html(gettext("No data available."));
          horizon.alert("error", gettext("An error occurred. Please try again later."));
        },
        complete: function (data, textStatus, jqXHR) {
          jquery_element.spin(false);
        }
      });
    }

  },

  refresh: function(html_element, data_series, data_type){
    var chart = new this.LineChart(this, html_element)
    // FIXME save chart objects somewhere so I can use them again when
    // e.g. I am switching tabs, or if I want to update them
    // via web sockets
    // this.charts.add_or_update(chart)
    chart.refresh(data_series, data_type);
  }
}

/* init the graphs */
horizon.addInitFunction(function () {
  horizon.d3_line_chart_resource.init("div[data-chart-type='line_chart_resource']");
});
