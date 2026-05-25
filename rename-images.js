/**
 * rename-images.js
 *
 * Renames local images based on product name from DB:
 *   "GB Softy Chocolate 145ml" + id 1489  →  gb.softy.chocolate.145ml.1489.jpg
 *
 * Usage:
 *   npm install pg
 *   node rename-images.js
 */

require("dotenv").config();

const pg   = require("pg");
const fs   = require("fs");
const path = require("path");

// ─── CONFIG ──────────────────────────────────────────────────────────────────
const CONFIG = {
    dbUrl:     process.env.SUPABASE_DB_URL,
    imagesDir: process.env.IMAGES_DIR      || "./images",
    baseUrl:   process.env.BASE_URL        || "https://assets.indiskaspicenord.com/images",
};
// ─────────────────────────────────────────────────────────────────────────────

/**
 * Build a clean filename from the product name + id.
 * - lowercase
 * - replace any run of non-alphanumeric chars with a single dot
 * - strip leading/trailing dots
 * e.g. "GB Softy Choc (145ml)" + 1489 → "gb.softy.choc.145ml.1489.jpg"
 */
function buildFilename(name, id, ext = ".jpg") {
    const slug = name
        .toLowerCase()
        .replace(/[^a-z0-9]+/g, ".") // non-alphanumeric runs → single dot
        .replace(/^\.+|\.+$/g, "");  // trim leading/trailing dots
    return `${slug}.${id}${ext}`;
}

async function main() {
    const client = new pg.Client({
        connectionString: CONFIG.dbUrl,
        ssl: { rejectUnauthorized: false },
    });

    try {
        await client.connect();
    } catch (err) {
        console.error("❌  Could not connect to Postgres:", err.message);
        process.exit(1);
    }
    console.log("✅  Connected to Postgres\n");

    // Fetch id, name, and current image (to find the existing local file)
    const { rows: products } = await client.query(
        "SELECT id, name, image FROM products WHERE image IS NOT NULL ORDER BY id"
    );
    console.log(`🔍  Found ${products.length} products with images.\n`);

    let renamed = 0;
    let skipped = 0;
    let errors  = 0;

    for (const { id, name, image } of products) {
        // Detect extension from existing image URL (default .jpg)
        const ext         = path.extname(path.basename(image)) || ".jpg";
        const newFilename = buildFilename(name, id, ext);
        const newImageUrl = `${CONFIG.baseUrl}/${newFilename}`;

        // Already correct in DB — check if local file also exists with new name
        if (image === newImageUrl) {
            console.log(`⏭️   [${id}] Already done: ${newFilename}`);
            skipped++;
            continue;
        }

        // Find the existing local file by its current URL basename
        const oldFilename = path.basename(image);
        const oldPath     = path.join(CONFIG.imagesDir, oldFilename);
        const newPath     = path.join(CONFIG.imagesDir, newFilename);

        if (!fs.existsSync(oldPath)) {
            console.warn(`⚠️   [${id}] Local file not found: ${oldPath}`);
            skipped++;
            continue;
        }

        // ── Rename locally ───────────────────────────────────────────────────────
        try {
            fs.renameSync(oldPath, newPath);
            console.log(`📁   [${image}] ->`);
            console.log(`📁   [${id}] ${oldFilename}`);
            console.log(`        →  ${newFilename}`);
        } catch (fsErr) {
            console.error(`❌  [${id}] Rename failed: ${fsErr.message}`);
            errors++;
            continue;
        }

        // ── Update DB ────────────────────────────────────────────────────────────
        try {
            await client.query(
                "UPDATE products SET image_backup = $1 WHERE id = $2",
                [newImageUrl, id]
            );
            console.log(`🗄️   [${id}] DB → ${newImageUrl}\n`);
            renamed++;
        } catch (dbErr) {
            console.error(`❌  [${id}] DB update failed: ${dbErr.message} — rolling back…`);
            try { fs.renameSync(newPath, oldPath); } catch (_) {}
            errors++;
        }
    }

    await client.end();

    console.log("─────────────────────────────────────────");
    console.log(`✅  Renamed & updated : ${renamed}`);
    console.log(`⏭️   Skipped           : ${skipped}`);
    console.log(`❌  Errors            : ${errors}`);
    console.log("─────────────────────────────────────────");
}

main().catch((err) => {
    console.error("Fatal:", err.message);
    process.exit(1);
});