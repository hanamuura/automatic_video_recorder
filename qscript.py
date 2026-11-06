import os
import re
import shutil
import tempfile
from pathlib import Path
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
from playwright.sync_api import sync_playwright


PATH_TO_VIDEO_FOLDER = "./video"
_ACTIVE_PAGE = None

def ShowCallout(text, bgColor, textColor, fade):
    page = _ACTIVE_PAGE

    if page is None:
        raise RuntimeError(
            "ShowCallout can only be used during an active recording"
        )
    page.evaluate(
        """({text, bgColor, textColor, fade}) => {
            const old = document.getElementById("__automation_callout");

            if (old) {
                old.remove();
            }

            const box = document.createElement("div");

            box.id = "__automation_callout";
            box.textContent = text;

            Object.assign(box.style, {
                position: "fixed",
                zIndex: "2147483647",
                left: "50%",
                top: "24px",
                transform: "translateX(-50%)",
                width: "max-content",
                maxWidth: "80vw",
                boxSizing: "border-box",
                padding: "12px 18px",
                border: "2px solid #111",
                borderRadius: "4px",
                background: bgColor,
                color: textColor,
                font: "16pt Arial, sans-serif",
                textAlign: "center",
                whiteSpace: "normal",
                pointerEvents: "none",
                opacity: fade ? "0" : "1",
                transition: fade ? "opacity 2s ease" : "none"
            });

            document.body.appendChild(box);

            if (fade) {
                requestAnimationFrame(() => {
                    box.style.opacity = "1";
                });

                window.setTimeout(() => {
                    box.style.opacity = "0";

                    window.setTimeout(() => {
                        box.remove();
                    }, 2050);

                }, 2500);

            } else {
                window.setTimeout(() => {
                    box.remove();
                }, 3500);
            }
        }""",
        {
            "text": str(text),
            "bgColor": str(bgColor),
            "textColor": str(textColor),
            "fade": bool(fade)
        }
    )

def _safe_filename(value):
    name = re.sub(
        r'[<>:"/\\|?*\x00-\x1f]',
        "_",
        str(value)
    ).strip(" .")
    return name or "recording"

def _move_cursor_smoothly(page, x, y, steps=28):
    page.mouse.move(x, y, steps=steps)

def _move_to_locator(page, locator):
    locator.wait_for(
        state="visible",
        timeout=30000
    )
    box = locator.bounding_box()

    if not box:
        raise RuntimeError(
            "Target element has no visible bounding box"
        )
    x = box["x"] + box["width"] / 2
    y = box["y"] + box["height"] / 2

    _move_cursor_smoothly(page, x, y)

    return x, y


def CaptureVideo_Magento(
    url,
    company_name,
    language,
    country,
    postcode,
    city,
    street,
    house_no,
):
    global _ACTIVE_PAGE

    video_folder = Path(
        PATH_TO_VIDEO_FOLDER
    ).expanduser().resolve()
    video_folder.mkdir(
        parents=True,
        exist_ok=True
    )
    recording_dir = Path(
        tempfile.mkdtemp(
            prefix=".recording_",
            dir=str(video_folder)
        )
    )
    browser = None
    context = None
    final_path = video_folder / (
        _safe_filename(company_name) + ".webm"
    )
    completed = False

    try:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(
                headless=False,
                slow_mo=50
            )
            context = browser.new_context(
                viewport={
                    "width": 1280,
                    "height": 720
                },
                record_video_dir=str(recording_dir),
                record_video_size={
                    "width": 1280,
                    "height": 720
                },
                locale="en-US",
                timezone_id="Europe/Berlin"
            )
            context.add_init_script(
                """(() => {

                    const install = () => {

                        if (
                            !document.documentElement ||
                            document.getElementById("__automation_cursor")
                        ) {
                            return;
                        }

                        const style = document.createElement("style");

                        style.textContent = `

                            #__automation_cursor,
                            #__automation_cursor_halo {
                                position: fixed;
                                left: 0;
                                top: 0;
                                pointer-events: none;
                                transform: translate3d(-100px,-100px,0);
                            }

                            #__automation_cursor_halo {
                                z-index: 2147483645;
                                width: 64px;
                                height: 64px;
                                margin-left: -32px;
                                margin-top: -32px;
                                border-radius: 50%;
                                background: rgba(255, 220, 0, .30);
                            }

                            #__automation_cursor {
                                z-index: 2147483646;
                                width: 32px;
                                height: 32px;
                                margin-left: 0;
                                margin-top: 0;
                                overflow: visible;
                            }

                            .__automation_ripple {
                                position: fixed;
                                z-index: 2147483644;
                                width: 8px;
                                height: 8px;
                                margin: -4px 0 0 -4px;
                                border: 2px solid rgba(255,190,0,.95);
                                border-radius: 50%;
                                pointer-events: none;
                                animation:
                                    __automation_ripple_anim
                                    .55s ease-out forwards;
                            }

                            @keyframes __automation_ripple_anim {

                                from {
                                    transform: scale(.2);
                                    opacity: 1;
                                }

                                to {
                                    transform: scale(8);
                                    opacity: 0;
                                }

                            }

                        `;

                        (
                            document.head ||
                            document.documentElement
                        ).appendChild(style);

                        const halo = document.createElement("div");

                        halo.id = "__automation_cursor_halo";

                        const cursor = document.createElementNS(
                            "http://www.w3.org/2000/svg",
                            "svg"
                        );

                        cursor.id = "__automation_cursor";

                        cursor.setAttribute(
                            "viewBox",
                            "0 0 32 32"
                        );

                        cursor.innerHTML = `
                            <path
                                d="M2 1 L2 26 L9 19 L14 30 L19 28 L14 17 L25 17 Z"
                                fill="white"
                                stroke="black"
                                stroke-width="1.7"
                                stroke-linejoin="round"
                            />
                        `;

                        document.documentElement.appendChild(halo);
                        document.documentElement.appendChild(cursor);

                        document.addEventListener(
                            "mousemove",
                            event => {

                                const transform =
                                    `translate3d(
                                        ${event.clientX}px,
                                        ${event.clientY}px,
                                        0
                                    )`;

                                halo.style.transform = transform;
                                cursor.style.transform = transform;

                            },
                            true
                        );

                        document.addEventListener(
                            "click",
                            event => {

                                const ripple = document.createElement("div");

                                ripple.className =
                                    "__automation_ripple";

                                ripple.style.left =
                                    event.clientX + "px";

                                ripple.style.top =
                                    event.clientY + "px";

                                document.documentElement.appendChild(
                                    ripple
                                );

                                window.setTimeout(() => {
                                    ripple.remove();
                                }, 650);

                            },
                            true
                        );

                    };

                    if (document.documentElement) {
                        install();
                    } else {
                        document.addEventListener(
                            "DOMContentLoaded",
                            install,
                            { once: true }
                        );
                    }

                })();"""
            )

            page = context.new_page()

            _ACTIVE_PAGE = page
            page.goto(
                str(url),
                wait_until="domcontentloaded",
                timeout=60000
            )
            page.wait_for_timeout(900)

            ShowCallout(
                "Searching for Magento developers",
                "yellow",
                "black",
                True
            )

            search_box = page.locator(
                'textarea[name="q"]'
            )
            search_x, search_y = _move_to_locator(
                page,
                search_box
            )
            page.mouse.click(
                search_x,
                search_y
            )
            page.wait_for_timeout(250)

            query = (
                "Magento developer in " + str(city)
            )

            page.keyboard.press("Control+A")
            page.keyboard.type(
                query,
                delay=105
            )

            submit_buttons = page.locator(
                'form button[type="submit"]'
                # 'cr-button[id=composeButton], '
                # 'div[class="bvUkz"]' #TODO: For google now dont work. Need to update this
            )
            submit_buttons.first.wait_for(
                state="attached",
                timeout=15000
            )

            if submit_buttons.count() > 1:
                search_button = submit_buttons.last
            else:
                search_button = submit_buttons.first

            button_x, button_y = _move_to_locator(
                page,
                search_button
            )
            page.wait_for_timeout(300)
            page.mouse.click(
                button_x,
                button_y
            )
            results = page.locator(
                'a[data-testid="result-title-a"]'
            )
            results.first.wait_for(
                state="visible",
                timeout=45000
            )
            page.wait_for_timeout(1200)
            first_x, first_y = _move_to_locator(
                page,
                results.first
            )
            ShowCallout(
                "Opening the first search result",
                "yellow",
                "black",
                True
            )
            page.wait_for_timeout(350)
            page.mouse.click(
                first_x,
                first_y
            )

            try:
                page.wait_for_load_state(
                    "domcontentloaded",
                    timeout=15000
                )
            except PlaywrightTimeoutError:
                pass

            page.wait_for_timeout(1200)

            context.close()
            context = None

            completed = True
    except Exception as exc:
        print(
            "Capture failed for {!r}: {}".format(
                company_name,
                exc
            )
        )
        completed = False
    finally:
        _ACTIVE_PAGE = None
        try:
            if context is not None:
                context.close()
        except Exception:
            completed = False
        try:
            if browser is not None:
                browser.close()
        except Exception:
            pass
    try:
        video_files = list(
            recording_dir.glob("*.webm")
        )
        if completed and video_files:
            source = max(
                video_files,
                key=lambda item: item.stat().st_mtime
            )
            os.replace(
                str(source),
                str(final_path)
            )
            return str(final_path.resolve())
    except Exception as exc:
        print(
            "Could not finalize video for {!r}: {}".format(
                company_name,
                exc
            )
        )
    finally:
        shutil.rmtree(
            str(recording_dir),
            ignore_errors=True
        )
    return None