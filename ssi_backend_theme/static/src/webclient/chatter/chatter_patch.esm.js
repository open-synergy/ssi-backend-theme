// Copyright 2026 OpenSynergy Indonesia
// Copyright 2026 PT. Simetri Sinergi Indonesia
// License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
import {append, combineAttributes, createElement} from "@web/core/utils/xml";
import {
    getEffectiveChatterPosition,
    getShowChatterToggle,
} from "./chatter_position.esm";
import {FormCompiler} from "@web/views/form/form_compiler";
import {FormRenderer} from "@web/views/form/form_renderer";
import {patch} from "@web/core/utils/patch";
import {useState} from "@odoo/owl";

// `mail`'s own `FormRenderer.prototype.mailLayout()` (mail/static/src/
// chatter/web/form_renderer.js) returns one of these five tags, and
// `mail`'s own `FormCompiler.prototype.compile()` (form_compiler.js in the
// same folder) turns each tag into CSS classes on the chatter wrapper
// (".o-aside" for a side column, "mt-4 mt-md-0" for a bottom band) -- never
// a different DOM structure. Remapping the *tag* here, instead of
// re-implementing `mailLayout()`'s own branching, is what keeps this patch
// narrow and resilient to unrelated changes in that branching (Keputusan
// Desain, issue #19: CSS classes on the wrapper, not core internals).
// "auto"/small-viewport calls are never remapped at all -- `super.
// mailLayout()`'s own tag is returned untouched in that case.
const TO_SIDE_TAG = {
    BOTTOM_CHATTER: "SIDE_CHATTER",
    EXTERNAL_COMBO: "EXTERNAL_COMBO_XXL",
};
const TO_BOTTOM_TAG = {
    SIDE_CHATTER: "BOTTOM_CHATTER",
    COMBO: "BOTTOM_CHATTER",
    EXTERNAL_COMBO_XXL: "EXTERNAL_COMBO",
};

patch(FormRenderer.prototype, {
    setup() {
        super.setup();
        // Never persisted (Keputusan Desain, issue #19): a plain OWL
        // `useState`, reset every time a new FormRenderer instance mounts
        // (i.e. every time a form is opened), exactly matching "state
        // hanya berlaku selama sesi tampilan".
        this.ssiChatterToggleState = useState({folded: false});
    },

    /**
     * @returns {Boolean}
     */
    get ssiShowChatterToggle() {
        return getShowChatterToggle();
    },

    /**
     * @returns {Boolean}
     */
    get ssiChatterFolded() {
        return this.ssiShowChatterToggle && this.ssiChatterToggleState.folded;
    },

    ssiToggleChatterFold() {
        this.ssiChatterToggleState.folded = !this.ssiChatterToggleState.folded;
    },

    mailLayout(hasAttachmentContainer) {
        const layout = super.mailLayout(hasAttachmentContainer);
        // Mobile has its own chatter layout and is never touched here
        // (Keputusan Desain, issue #19) -- `env.isSmall` is the same
        // breakpoint core itself already uses to branch entire form-view
        // components between desktop/mobile (e.g. web/static/src/views/
        // form/form_renderer.js, form_cog_menu.xml).
        if (this.env.isSmall) {
            return layout;
        }
        const position = getEffectiveChatterPosition();
        if (position === "right") {
            return TO_SIDE_TAG[layout] || layout;
        }
        if (position === "bottom") {
            return TO_BOTTOM_TAG[layout] || layout;
        }
        // "auto"
        return layout;
    },
});

patch(FormCompiler.prototype, {
    compile(node, params) {
        const res = super.compile(node, params);
        const chatterContainerHookXml = res.querySelector(".o-mail-Form-chatter");
        if (!chatterContainerHookXml) {
            // No chatter on this view, nothing to add.
            return res;
        }
        // Adds to the "t-attf-class" mail's own patch already set on this
        // same element (see form_compiler.js: "o-aside w-print-100" /
        // "mt-4 mt-md-0") -- `combineAttributes` joins both `{{ }}`
        // expressions with a space, never replacing mail's own one.
        combineAttributes(
            chatterContainerHookXml,
            "t-attf-class",
            '{{ __comp__.ssiChatterFolded ? "o_ssi_chatter_folded" : "" }}'
        );
        // A single toggle button, attached inside the chatter's own
        // wrapper (never inside `mail.Chatter` itself, so it never
        // renders in dialogs/kanban attachment previews -- Keputusan
        // Desain, issue #19 scopes this to the form view only) and
        // positioned with CSS alone (chatter_patch.scss); no DOM
        // restructuring of the wrapper's existing (only) child.
        const toggleButtonXml = createElement("button", {
            type: "button",
            class: "o_ssi_chatter_toggle btn btn-sm btn-link",
            "t-if": "__comp__.ssiShowChatterToggle",
            "t-on-click": "() => __comp__.ssiToggleChatterFold()",
            "t-att-title":
                '__comp__.ssiChatterFolded ? "Show Chatter" : "Hide Chatter"',
            "t-att-aria-label":
                '__comp__.ssiChatterFolded ? "Show Chatter" : "Hide Chatter"',
        });
        const iconXml = createElement("i", {
            class: "fa",
            "t-attf-class":
                '{{ __comp__.ssiChatterFolded ? "fa-comments" : "fa-times" }}',
        });
        append(toggleButtonXml, iconXml);
        append(chatterContainerHookXml, toggleButtonXml);
        return res;
    },
});
