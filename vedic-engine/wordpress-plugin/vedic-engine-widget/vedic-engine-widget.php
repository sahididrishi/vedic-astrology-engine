<?php
/**
 * Plugin Name: Vedic Engine Widget
 * Description: Embeds the Vedic Astrology Predictive Engine as a shortcode form.
 * Version: 1.0.0
 * Author: Vedic Engine
 */

defined('ABSPATH') || exit;

add_shortcode('vedic_reading', 've_render_form');

function ve_render_form() {
    $api_url = get_option('ve_api_url', 'https://your-engine-domain.com/api/v1/reading');
    ob_start(); ?>
    <div id="ve-widget" style="max-width:520px;font-family:sans-serif;">
      <form id="ve-form">
        <div style="margin-bottom:12px">
          <label>Full name</label><br>
          <input type="text" name="full_name" required style="width:100%;padding:8px;border:1px solid #ccc;border-radius:6px">
        </div>
        <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;margin-bottom:12px">
          <div>
            <label>Birth date</label><br>
            <input type="date" name="birth_date" required style="width:100%;padding:8px;border:1px solid #ccc;border-radius:6px">
          </div>
          <div>
            <label>Birth time</label><br>
            <input type="time" name="birth_time" required style="width:100%;padding:8px;border:1px solid #ccc;border-radius:6px">
          </div>
        </div>
        <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;margin-bottom:12px">
          <div>
            <label>Birth city</label><br>
            <input type="text" name="birth_city" required placeholder="e.g. Mumbai" style="width:100%;padding:8px;border:1px solid #ccc;border-radius:6px">
          </div>
          <div>
            <label>Country</label><br>
            <input type="text" name="birth_country" required placeholder="e.g. India" style="width:100%;padding:8px;border:1px solid #ccc;border-radius:6px">
          </div>
        </div>
        <div style="margin-bottom:16px">
          <label>Reading focus</label><br>
          <select name="reading_type" style="width:100%;padding:8px;border:1px solid #ccc;border-radius:6px">
            <option value="general">General life reading</option>
            <option value="career">Career &amp; purpose</option>
            <option value="relationships">Relationships</option>
            <option value="finance">Finance &amp; wealth</option>
            <option value="health">Health &amp; wellbeing</option>
          </select>
        </div>
        <button type="submit" id="ve-submit" style="width:100%;padding:10px;background:#1a1a2e;color:white;border:none;border-radius:6px;font-size:15px;cursor:pointer">
          Get my reading
        </button>
      </form>
      <div id="ve-result" style="display:none;margin-top:24px"></div>
      <div id="ve-error" style="display:none;color:#c0392b;margin-top:12px;font-size:13px"></div>
    </div>
    <script>
    document.getElementById('ve-form').addEventListener('submit', async function(e) {
      e.preventDefault();
      var btn = document.getElementById('ve-submit');
      var result = document.getElementById('ve-result');
      var errBox = document.getElementById('ve-error');
      btn.textContent = 'Generating reading...';
      btn.disabled = true;
      errBox.style.display = 'none';
      var fd = new FormData(e.target);
      var payload = Object.fromEntries(fd.entries());
      try {
        var resp = await fetch('<?php echo esc_url($api_url); ?>', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': 'Bearer <?php echo esc_js(get_option("ve_api_key", "")); ?>'
          },
          body: JSON.stringify(payload)
        });
        if (!resp.ok) throw new Error('API error: ' + resp.status);
        var data = await resp.json();
        result.style.display = 'block';
        result.innerHTML = renderReading(data);
      } catch(err) {
        errBox.style.display = 'block';
        errBox.textContent = 'Error: ' + err.message;
      } finally {
        btn.textContent = 'Get my reading';
        btn.disabled = false;
      }
    });

    function renderReading(data) {
      var html = '<div style="border-top:2px solid #1a1a2e;padding-top:16px">';
      html += '<p style="font-size:15px;color:#333;margin-bottom:16px">' + esc(data.overview) + '</p>';
      (data.sections || []).forEach(function(s) {
        html += '<div style="margin-bottom:20px">';
        html += '<h3 style="font-size:14px;font-weight:600;text-transform:uppercase;letter-spacing:.05em;color:#1a1a2e;margin-bottom:6px">' + esc(s.title) + '</h3>';
        html += '<p style="font-size:14px;color:#444;line-height:1.7">' + esc(s.insight) + '</p>';
        if (s.actions && s.actions.length) {
          html += '<ul style="margin-top:8px;padding-left:18px">';
          s.actions.forEach(function(a) { html += '<li style="font-size:13px;color:#555;margin-bottom:4px">' + esc(a) + '</li>'; });
          html += '</ul>';
        }
        html += '</div>';
      });
      if (data.key_periods && data.key_periods.length) {
        html += '<div style="background:#f8f8f8;border-radius:8px;padding:14px;margin-bottom:16px">';
        html += '<h3 style="font-size:13px;font-weight:600;text-transform:uppercase;color:#888;margin-bottom:10px">Key periods ahead</h3>';
        data.key_periods.forEach(function(kp) {
          html += '<div style="margin-bottom:8px"><span style="font-weight:600;font-size:13px">' + esc(kp.period) + '</span>';
          html += ' &mdash; <span style="font-size:13px;color:#555">' + esc(kp.theme) + ': ' + esc(kp.guidance) + '</span></div>';
        });
        html += '</div>';
      }
      html += '<p style="font-size:14px;color:#555;font-style:italic;border-top:1px solid #eee;padding-top:12px">' + esc(data.closing) + '</p>';
      html += '</div>';
      return html;
    }

    function esc(s) {
      if (!s) return '';
      var d = document.createElement('div');
      d.appendChild(document.createTextNode(s));
      return d.innerHTML;
    }
    </script>
    <?php
    return ob_get_clean();
}

add_action('admin_menu', function() {
    add_options_page('Vedic Engine', 'Vedic Engine', 'manage_options', 've-settings', 've_settings_page');
});

function ve_settings_page() { ?>
    <div class="wrap">
      <h1>Vedic Engine Settings</h1>
      <form method="post" action="options.php">
        <?php settings_fields('ve_settings_group'); do_settings_sections('ve-settings'); ?>
        <table class="form-table">
          <tr><th>API URL</th><td><input type="url" name="ve_api_url" value="<?php echo esc_attr(get_option('ve_api_url')); ?>" style="width:400px"></td></tr>
          <tr><th>API Key</th><td><input type="password" name="ve_api_key" value="<?php echo esc_attr(get_option('ve_api_key')); ?>" style="width:400px"></td></tr>
        </table>
        <?php submit_button(); ?>
      </form>
    </div>
<?php }

add_action('admin_init', function() {
    register_setting('ve_settings_group', 've_api_url');
    register_setting('ve_settings_group', 've_api_key');
});
