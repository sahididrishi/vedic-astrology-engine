<?php
/**
 * Plugin Name: Vedic Engine Widget
 * Description: Embeds the Vedic Astrology Predictive Engine as a shortcode form.
 * Version: 1.1.0
 * Author: Vedic Engine
 */

defined('ABSPATH') || exit;

// ── AJAX proxy — API key stays server-side, never in browser HTML ────────

add_action('wp_ajax_ve_reading', 've_proxy_reading');
add_action('wp_ajax_nopriv_ve_reading', 've_proxy_reading');

function ve_proxy_reading() {
    // Verify nonce to prevent CSRF
    if (!isset($_POST['nonce']) || !wp_verify_nonce($_POST['nonce'], 've_reading_nonce')) {
        wp_send_json_error(['message' => 'Security check failed'], 403);
    }

    $api_url = get_option('ve_api_url', '');
    $api_key = get_option('ve_api_key', '');

    if (empty($api_url) || empty($api_key)) {
        wp_send_json_error(['message' => 'Vedic Engine not configured. Set API URL and key in Settings.'], 500);
    }

    // Read JSON body from the request
    $raw_body = file_get_contents('php://input');
    // If body is empty, build from POST data
    if (empty($raw_body) || $raw_body === '{}') {
        $fields = ['full_name', 'birth_date', 'birth_time', 'birth_city', 'birth_country', 'reading_type'];
        $payload = [];
        foreach ($fields as $f) {
            if (isset($_POST[$f])) {
                $payload[$f] = sanitize_text_field($_POST[$f]);
            }
        }
        $raw_body = wp_json_encode($payload);
    }

    $response = wp_remote_post($api_url, [
        'headers' => [
            'Content-Type'  => 'application/json',
            'Authorization' => 'Bearer ' . $api_key,
        ],
        'body'    => $raw_body,
        'timeout' => 35,
    ]);

    if (is_wp_error($response)) {
        wp_send_json_error(['message' => $response->get_error_message()], 502);
    }

    $status = wp_remote_retrieve_response_code($response);
    $body   = json_decode(wp_remote_retrieve_body($response), true);

    wp_send_json($body, $status);
}

// ── Shortcode ────────────────────────────────────────────────────────────

add_shortcode('vedic_reading', 've_render_form');

function ve_render_form() {
    // Pass AJAX URL and nonce to the frontend (no API key!)
    $ajax_url = admin_url('admin-ajax.php');
    $nonce    = wp_create_nonce('ve_reading_nonce');

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
    (function() {
      var ajaxUrl = <?php echo wp_json_encode($ajax_url); ?>;
      var nonce   = <?php echo wp_json_encode($nonce); ?>;

      document.getElementById('ve-form').addEventListener('submit', async function(e) {
        e.preventDefault();
        var btn = document.getElementById('ve-submit');
        var result = document.getElementById('ve-result');
        var errBox = document.getElementById('ve-error');
        btn.textContent = 'Generating reading...';
        btn.disabled = true;
        errBox.style.display = 'none';

        var fd = new FormData(e.target);
        fd.append('action', 've_reading');
        fd.append('nonce', nonce);

        try {
          var resp = await fetch(ajaxUrl, { method: 'POST', body: fd });
          if (!resp.ok) {
            var errData = await resp.json().catch(function() { return {}; });
            throw new Error(errData.message || errData.data?.message || 'API error: ' + resp.status);
          }
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
    })();
    </script>
    <?php
    return ob_get_clean();
}

// ── Settings page ────────────────────────────────────────────────────────

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
    register_setting('ve_settings_group', 've_api_url', [
        'sanitize_callback' => 'esc_url_raw',
    ]);
    register_setting('ve_settings_group', 've_api_key', [
        'sanitize_callback' => 'sanitize_text_field',
    ]);
});
