Title: Infusion and JSON Schemas, Part 4: End User Feedback, Redux
Date: 2018-03-26 15:30
Category: Code
Tags: JSON Schema
Slug: infusion-and-json-schema-feedback-two
Author: Tony Atkins <tony@raisingthefloor.org>
Summary: An updated discussion of the issues involved in providing end-user feedback when validation options using a JSON Schema.

# Introduction #

In previous posts like [this one]({filename}./end-user-feedback.md), I wrote about a JSON (meta)schema-based approach to
adding key information useful in working with JSON Schemas and UIs:

1. Expressing UI hints such as instructions and field labels that should be displayed near an input or control.
2. Customising raw validation errors, for example, by replacing them with localised or internationalised output.
3. Internationalising and localising both of the above.

The core standard does not provide a means to accomplish either.  There are various efforts to add error specific or UI
specific keywords, but in order to accomplish this properly, we would need to create and maintain a metaschema
[as outlined here]({filename}./end-user-feedback.md).  This is non-trivial work, as it requires:

- Carefully reviewing each draft of the JSON Schema standard and reusing definitions from it in a new metaschema.
- Working carefully to preserve the type of circular references used in the underlying draft standard (every object may contain objects, for example).
- Testing our metaschema with various validators.

In recent discussions, we have leaned more towards storing i18n message keys within component options.  In addition to
helping us avoid the work of writing and maintaining metaschemas, this approach is also more natural for experienced
component authors vs. expressing UI concerns in a new format, one that is not immediately visible when working with the
component itself.

This article reviews the information provided by our current validator, and outlines how we might use that in
combination in a "component-centric" approach.

# Providing UI Hints #

Let's start with a simpler use case, adding UI hints (instructions, labels, etc.) to a schema.  As we do not have to
ever deal with validator output or JSON Pointers, we can use a similar model to gpii-binder, and provide both a "short"
and a "long" strategy for describing the "path to variable" and the UI metadata, as in this crude mockup:

```javascript
fluid.defaults("my.ui.grade.short", {
    gradeNames: ["fluid.ViewComponent"],
    hints: {
        "path.to.variable": "i18n-key-for-variable-hint"
    }
});

fluid.defaults("my.ui.grade.long", {
    gradeNames: ["fluid.ViewComponent"],
    hints: {
        "myHint": {
            modelPath: "path.to.variable",
            hintKey: "i18n-key-for-variable-hint"
        }
    }
});

```

However we choose to assemble message bundles, the "hints" are defined in the same way, i.e. as message keys.

One issue we have not addressed with regards to gpii-binder is merging "short" and "long" notations, we should discuss
whether a "short" notation is valuable enough to make it worth writing function(s) to handle the merging of the above
examples.

# Evolving Validation Errors #

## AJV ##

Before we can discuss how we might localise and/or internationalise validation errors, we should understand what they
look like by default.  We currently use the validator [AJV](https://github.com/epoberezkin/ajv), so I wanted to use that
to provide some sample validation errors and talk about the key concerns.  For the first two examples, let's assume
we're using a schema like the following:

```json
{
    "$schema": "http://json-schema.org/draft-07/schema#",
    "title": "Deep schema to test variable nesting and paths.",
    "type":  "object",
    "properties": {
        "deep": {
            "type": "object",
            "properties": {
                "required": {
                    "type": "boolean"
                }
            },
            "required": ["required"]
        }
    }
}
```
Let's say we try to validate the following:

```json
{
     "required": true,
     "deep": { "required": "a string" }
}
```

AJV returns an error like:

```json
{
  "keyword": "type",
  "dataPath": ".deep.required",
  "schemaPath": "#/properties/deep/properties/required/type",
  "params": {
    "type": "boolean"
  },
  "message": "should be boolean"
}
```

The `dataPath` is the path to the failing data.  With the exception of the leading dot, that path closely matches an EL
path relative to the root of the object that was validated.  The `schemaPath` value represents the path to the rule that
was broken.  This is a JSON Pointer expressed relative to the root of the schema (#).   In the example above, that JSON
Pointer resolves to the string `"boolean"`.  The `message` value purports to give details about the validation error,
but is expressed in English sentence fragments that are especially hairy when dealing with regular expression pattern
matching failures, as in this example from the tests in the gpii-json-schema package:

```json
{
    "keyword": "pattern",
    "dataPath": ".rawMultiple",
    "schemaPath": "#/properties/rawMultiple/allOf/1/pattern",
    "params": {
        "pattern": "[A-Z]+"
    },
    "message": "should match pattern \"[A-Z]+\""
}
```

Here's another example for the same schema mentioned earlier in this section.  Let's say we leave out the "deep" required field and attempt to validate
the following:

```json
{
     "required": true
}
```

AJV reports an error like the following:

```json
{
  "keyword": "required",
  "dataPath": ".deep",
  "schemaPath": "#/properties/deep/required",
  "params": {
    "missingProperty": "required"
  },
  "message": "should have required property 'required'"
}
```

This demonstrates a key point.  Since draft v4 of the standard, JSON Schemas define missing required fields in terms of
the containing element (previously each field had a true/false `required` property).  The `schemaPath` in this case is
relative to the enclosing object, and the JSON pointer points to the array of ALL required fields, i.e. there is no
effort made to say that required field #2 is the specific field that's missing.

There is also the special case of the "anyOf" and "allOf" constructs, which are arrays where the index of the failing
rule is considered.  Let's say we have a schema like the following:

```json
{
    "$schema": "http://json-schema.org/draft-07/schema#",
    "id":      "password.json",
    "title":   "Password Validation Schema",
    "type":    "object",
    "properties": {
        "password": {
          "description": "Password must be 8 or more characters, and have at least one uppercase letter, at least one lowercase letter, and at least one number or special character.",
          "allOf": [
            { "type": "string", "minLength": 8 },
            { "type": "string", "pattern": "[A-Z]+"},
            { "type": "string", "pattern": "[a-z]+"},
            { "type": "string", "pattern": "[^a-zA-Z]"}
          ]
        }
  },
     "required": ["password"]

}
```

Let's say we try to validate the following:

```json
{ "password": "2Short" }
```

AJV will return an error like:

```json
{
  "keyword": "minLength",
  "dataPath": ".password",
  "schemaPath": "#/properties/password/allOf/0/minLength",
  "params": {
    "limit": 8
  },
  "message": "should NOT be shorter than 8 characters"
}
```

The `schemaPath` pointer refers to the numeric value `8`.

# Standardising Validation Errors #

Now that we know what we have (at least if we choose to continue using AJV), let's talk about the key questions we need
to be able to answer:

1. What information is invalid?
2. What rule(s) does it break?

We can fairly easily represent the path to the invalid information. A simple transform of the `dataPath` value can
produce an EL path that can be used to find the offending value using `fluid.get`.  This breaks down somewhat when
dealing with required fields, but can use a slightly more complex transform to standardise those paths.

Things get more complex when we want to represent which rule(s) were broken.  We can start to simplify the problem space
by constructing a JSON Schema snippet that represents the failing rule.  We can do this by looking at the last segment
of the `schemaPath` JSON Pointer (or AJV's equivalent `keyword` value) and the value that the `schemaPath` pointer
references within the schema, as in:

`{ "type": "boolean"} // #/properties/deep/properties/required/type => "boolean" `
`{ "minLength": 8}    // #/properties/password/allOf/0/minLength => 8 `


As each of these failing rules will ultimately reduce to a keyword representing the broken rule, our intermediate
validation error format might look like:

```json
{
    "failurePath": "deep.required",
    "rule": { "type": "boolean" }
}
```

Once we have flattened out the failures relative to the failing material, we can represent error message keys using
notation like the following (again, both "short" and "long" examples are provided):

```javascript
fluid.defaults("my.validating.component", {
    gradeNames: ["fluid.component"],
    errors: {
        "mailOptions.sender": "sender-invalid-generic-message-key", // "short" notation for all errors.
        "mailOptions.recipient": { // "long" notation
            "format": "recipient-invalid-format-invalid-key", // Custom message for a specific error.
            "": "recipient-invalid-key" // We can still provide a single message for all remaining errors.
        }
    },
    messages: {
        "recipient-invalid-format-invalid-key": "The email address '%mailOptions.recipient' is invalid."
    }
})
```

The validator can still return the specifics of the failing rule, but component authors would only have to be aware of:

1. The EL path to the failing material.
2. The message key they wish to use in place of the underlying error.
3. (Optionally) Specific validation keywords they wish to provide separate error messages for.

The message templates themselves should be able to include variables that refer to the offending material.  Rather than
deal in relative paths, I would suggest that all string templates for error messages use the full EL path within the
object being validated, as shown above.  This offers good flexibility versus schemes like only offering access to the
failing data itself.

## Required Fields ##

So, how do we deal with the special case of required fields?  I would suggest that our intermediate validation error
format follow the JSON Schema draft v3 convention, and make `required` a property of the missing material itself, as in:

```json
{
    "failurePath": "path.to.requiredField",
    "rule": { "required": true}
}
```

We can then represent all variations relative to the missing material, as in:

```javascript
fluid.defaults("my.validating.component", {
    gradeNames: ["fluid.component"],
    errors: {
        "mailOptions.sender": "sender-invalid-generic-message-key", // "short" notation for all errors.
        "mailOptions.recipient": { // "long" notation
            "format": "recipient-invalid-format-invalid-key", // Custom message for a specific error.
            "required": "recipient-required-key",
            "": "recipient-invalid-key" // We can still provide a single message for all remaining errors.
        }
    },
    messages: {
        "recipient-invalid-format-invalid-key": "The email address '%mailOptions.recipient' is invalid."
    }
})
```

As long as we can agree on this flattened structure, the authoring of error message hints becomes fairly
straightforward.

## "Dereferencing" Schemas ##

All of my examples above have presented schemas that define all properties directly.  Many schema
authors (including myself) follow the best practice of using "definitions" to allow easier reuse within the schema, and
from other schemas, as in:

```json
{
    "$schema": "http://json-schema.org/draft-07/schema#",
    "definitions": {
        "email": { "type": "string", "format": "email"}
    },
    "properties": {
        "from": { "$ref": "#/definitions/email" },
        "to":   { "$ref": "#/definitions/email" }
    }
}
```

In gpii-json-schema, we use [json-schema-deref](https://www.npmjs.com/package/json-schema-deref) to "dereference" this
into something like:

```json
{
    "$schema": "http://json-schema.org/draft-07/schema#",
    "definitions": {
        "email": { "type": "string", "format": "email"}
    },
    "properties": {
        "from": { "type": "string", "format": "email" },
        "to":   { "type": "string", "format": "email" }
    }
}
```

The `$ref` values used into the original are replaced with the full definition.  This allows us to more simply follow
the strategy outlined above of representing a rule that has been broken in terms of a schema snippet.

# Conclusion #

In summary, I am proposing that we:

1. Represent UI hints using a structure that relates "path to material" to the appropriate message key.
2. Represent validation error messages using a structure that relates "path to material" and "failing rule" to the appropriate message key.
3. Agree upon and transform the raw AJV output to our own validation error format.
4. Dereference schemas before using them for validation purposes.

My goal here is to provide a proposal as a starting point, and detailed enough examples to spur a good discussion.  I
plan to write up the group consensus and use that as part of upcoming work in the gpii-json-schema package.