Title: Infusion and JSON Schemas, Part 3: End User Feedback
Date: 2017-05-16 10:00
Category: Code
Slug: infusion-and-json-schema-feedback
Author: Tony Atkins <tony@raisingthefloor.org>
Summary: A detailed comparison of the issues involved in providing end-user feedback when validation options using a JSON Schema.

# Introduction

This page will cover a range of issues involved in presenting end-user feedback as users input data, based on fields
defined in a JSON schema and/or our own layer of component metadata.  For a general overview of the broader topic and 
use cases, please review the [{content}/infusion-and-json-schema/introduction.md](introduction).

In the three use cases we are concerned with at the moment, we need to be able to:

1. Provide human-readable instructions for a given field in a schema.
2. Provide human-readable feedback for validation errors.
3. Internationalise both of the above.

# Error Feedback

Validation tools like [AJV](https://github.com/epoberezkin/ajv) produce very detailed information about what particular
rule in the schema has been validated, and about the piece of the validated object that fails the check.  However, this
information is not typically in a form that is suitable for presenting to end users.  Here, for example, are a few error
messages returned by AJV:

```json
[
  {
    "keyword": "type",
    "dataPath": ".field1",
    "schemaPath": "base.json#field1/type",
    "params": {
      "type": "string"
    },
    "message": "should be string"
  },
  {
    "keyword": "required",
    "dataPath": "",
    "schemaPath": "#/required",
    "params": {
      "missingProperty": "field2"
    },
    "message": "should have required property 'field2'"
  }
]
```

For full details on the meaning of individual properties in the validation output, see
[the AJV documentation](https://github.com/epoberezkin/ajv#validation-errors).  For the purposes of this discussion, 
I will focus on the `dataPath`, `schemaPath`, and `message`  properties.

## `dataPath`

The `dataPath` field gives us a path to material within the validated content that failed to validate.  By default, 
`dataPath` is presented in a "Javascript object notation" format, which we can use with 
[`fluid.get`](http://docs.fluidproject.org/infusion/development/CoreAPI.html#fluid-get-model-path-)
(we would typically strip the leading dot).

Note that "required" fields are a special case, in that the enclosing object is the target, and not the missing field
itself.  This is a key side-effect of an early design decision regarding the JSON Schema standard.  As of draft v3,
[it was possible to specify within the field definition itself that the field was required](https://tools.ietf.org/html/draft-zyp-json-schema-03#section-5.7).
In draft v4 and beyond, the enclosing field is now responsible for indicating which fields are required.  In practice,
we will likely want to add special handling for "required" failures, so that we have the choice to display an 
error in the context of the missing field.  With AJV, we can do this by checking for a value in `params.missingProperty`.

## `schemaPath`

The `schemaPath` field gives us a [JSON pointer](https://tools.ietf.org/html/rfc6901) which points to the failing rule
within the schema.  If we have the full content of a given schema, we can use a tool like [`jsonpointer.js`](https://github.com/alexeykuzmin/jsonpointer.js/)
to retrieve details regarding the failing rule.  So, to continue the above example, the `schemaPath` `base.json#field1/type`
points to the value `string`.  In later examples we will discuss how we can use these pointers in combination with our 
own `keyword` to provide better end-user feedback.

So, to keep the example relatively simple, I have avoided using the `$ref` keyword discussed in the 
["reuse" article in this series]({filename}reusing-and-extending.md).  At least in `gpii-json-schema`, we 
[dereference](https://github.com/BigstickCarpet/json-schema-ref-parser/blob/master/docs/ref-parser.md#dereferenceschema-options-callback)
each schema before using it for validation.  Dereferencing replaces all `$ref` values with 
their linked definitions, and merges any local rules.  Regardless of how complex our reuse strategy is, it is as though
we had only ever used "simple" definitions.  This makes the `schemaPath` values more predictable, in that we will always
receive failures relative to a property or sub-property.  It also ensures that we ourselves do not need to look up
`$ref` values, which may point to external files and require additional network calls.

## `message`

This is the raw feedback on the failure, in string form.  It is typically not presented as a complete sentence, and
lacks capitalisation and punctuation.

Feedback like `should be string` is accurate, but typically we would rather provide more graceful feedback like `Please
enter a string`.  Feedback like `should have required property 'field2'` is more problematic, in that the feedback is
presented in terms of the raw field name within the object being validated, and not in terms of a label that is
meaningful to the end user, as in `You are required to enter an email address`.

As we will discuss below, the key in evolving this is to start with what we have (path within the validated object,
path to the failing rule) and overlay more human readable messages.


## `data`

In earlier versions of AJV, by default the failing data was also included under the `data` keyword.  So, for example,
validation errors for a password would routinely include the password as a string.  Thankfully this is now disabled by
default.

## Approach 1: Overlaying Error Information via Component Options

In this approach, we assume that we have a block of options which includes information about potential errors.  We can
either associate these messages with a path to options, or with the failing rule.  Although we will likely use
inheritance to abstract some of this out, for the purposes of clarity, I will write out all rules as though the complete
schema had already been dereferenced or otherwise reduced to simple rules.

## Approach 1a: "path to invalid option"

First, let's look at the "path to invalid option" approach, which might look like the following:

```javascript
fluid.defaults("gpii.schema.inline.withEvolvedErrors.viaDotPath", {
    gradeNames: ["gpii.schema.inline"],
    errorMessages: {
        "field1": "You must enter a string.",
        "deep.field2": "You must enter a number."
    },
    schema: {
        "$schema": "http://json-schema.org/schema#",
        properties: {
            field1: { type: "string" },
            deep: {
                properties: {
                    field2: { type: "number" }
                },
                required: ["field2"]
            },
            schema: {
                "$ref": "http://json-schema.org/schema#"
            },
            errorMessages: {
                "type": "object",
                "patternProperties": {
                    "[a-zA-Z0-9\.]+": { "type": "string" }
                },
                "additionalProperties": false
            }
        },
        required: ["field1", "deep"]
    }
});
```
A few notes on validating the error messages:  We haven't previously mentioned
[the `patternProperties` option](https://spacetelescope.github.io/understanding-json-schema/reference/object.html#pattern-properties),
which is used here to control what keys are acceptable.  It's likely that we would use a slightly more nuanced regexp
pattern, to protect against keys like `.` or `.path.to.content`.  We've indicated that the "right side" of each key/value
pair is a string, which means that deep structures are not allowed.

When dealing with validation errors other than "required field" errors, we would use `dataPath` (minus the leading dot,
see above)  to look up the error message, perhaps with some kind of templating.  For "required" field errors, we would
combine `dataPath` with `params.missingField` (see above) to look up the error message.

As we have discussed in meetings, this method sacrifices specificity for the sake of simplicity.  We would only be able
to specify one error message per field.  However, we would not have to specify one error for each rule, as is required
with approaches outlined below.

As was also pointed out in our meetings, this method further entangles actual options and metadata regarding options.
Instead of only having one field (`schema`) that must be validated by the schema itself, we would now have two
constructs (`schema` and `errorMessages`).

This method is also problematic with regards to reuse, in that error messages cannot be reused or inherited unless
the path exactly matches what is defined in `errorMessages`.

Although it isn't demonstrated here, templating can be easily added to this construct (and approach 1b) using existing
concepts like [`expanders`](http://docs.fluidproject.org/infusion/development/ExpansionOfComponentOptions.html#expanders).

### Approach 1b: "path to failing rule"

Let's look at the same example expressed in terms of the path (JSON pointer) to the failing rule:

```javascript
fluid.defaults("gpii.schema.inline.withEvolvedErrors.viaJsonPointer", {
    gradeNames: ["gpii.schema.inline"],
    errorMessages: {
        "#/properties/required/0": "You must enter a string.",
        "#/properties/field1/type": "You must enter a string.",
        "#/properties/deep/properties/required/0": "You must enter a number."
        "#/properties/deep/properties/field2/type": "You must enter a number."
    },
    schema: {
        "$schema": "http://json-schema.org/schema#",
        properties: {
            field1: { type: "string" },
            deep: {
                properties: {
                    field2: { type: "number" }
                },
                required: ["field2"]
            },
            schema: {
                "$ref": "http://json-schema.org/schema#"
            },
            errorMessages: {
                "type": "object",
                "patternProperties": {
                    "(http://)?([a-z]\.+/)\#[a-zA-Z0-9\/]+": { "type": "string" }
                },
                "additionalProperties": false
            }
        },
        required: ["field1", "deep"]
    }
});
```
The `patternProperties` regexp has not been tested at all, but is meant to suggest that we would require a relative
or absolute URI for the left hand side of the equation.  You can see in the above example that we now have specificity,
but that we now have to provide feedback for multiple rules.  We can mitigate this using expanders or IoC references,
but the format will still be more verbose than Approach 1a.

This approach has the unique advantage of allowing us to overlay messages on the deep structure of our rules.  This 
allows us to overlay internationalised messages on an existing schema, as shown in the following examples:

```javascript
fluid.defaults("gpii.schema.inline.withEvolvedErrors.viaJsonPointer.inline", {
    gradeNames: ["gpii.schema.inline.withEvolvedErrors.viaJsonPointer"],
    errorMessages: {
        "#/properties/required/0": "You must enter a string.",
        "#/properties/field1/type": "You must enter a string.",
        "#/properties/deep/properties/required/0": "You must enter a number.",
        "#/properties/deep/properties/field2/type": "You must enter a number."
    }
});

fluid.defaults("gpii.schema.inline.withEvolvedErrors.viaJsonPointer.external", {
    gradeNames: ["gpii.schema.external"],
    errorMessages: {
        "#/properties/required/0": "You must enter a string.",
        "#/properties/field1/type": "You must enter a string.",
        "#/properties/deep/properties/required/0": "You must enter a number.",
        "#/properties/deep/properties/field2/type": "You must enter a number."
    },
    schema: "http://my.site/schemas/external.json"
});

fluid.defaults("gpii.schema.inline.withEvolvedErrors.viaJsonPointer.hybrid", {
    gradeNames: ["gpii.schema.hybrid"],
    errorMessages: {
        "#/properties/required/0": "You must enter a string.",
        "#/properties/field1/type": "You must enter a string.",
        "#/properties/deep/properties/required/0": "You must enter a number.",
        "#/properties/deep/properties/field2/type": "You must enter a number."
    },
    schema: {
        "$schema": "http://json-schema.org/schema#",
        "$ref": "http://my.site/schemas/external.json"
    }
});
```
In the first "inline" example, we are merging options with an underlying grade, and simply overlaying error messages.
In the second "external" example, we point to an external JSON Schema and overlay our rules over that.  In the third
"hybrid" example, we point to the external schema within our options, and then overlay our rules as in all other
examples.

## Approach 2: Overlaying Error Information via One or More Custom Keywords

There are various ways of accomplishing this, but the general approach is the same:  make it possible to use new
keywords within the schema definition (inline or otherwise).  These keywords would define custom error messages in
the exact context of the failing rule, as shown in the following examples.

This is the rough approach that is under consideration as [a proposed JSON Schema UI extension](https://github.com/json-schema-org/json-schema-spec/issues/67
).
In the absence of a (proposed) standard, there are other projects that also follow similar a pattern of using custom keywords
within a schema.  For example, [react-jsonschema-form](https://github.com/mozilla-services/react-jsonschema-form),
which is highlighted here mainly because there is clear documentation and a live playground to help illustrate their
approach.

## Approach 2a: ajv-errors

The maintainer of AJV has recently released a library called [`ajv-errors`](https://github.com/epoberezkin/ajv-errors)
that adds a custom `errorMessages` keyword.  This is used as demonstrated below:


```json
{
  "$schema": "http://json-schema.org/schema#",
  "$id": "my-base-schema.json",
  "properties": {
    "field1": {
      "$id": "/field1",
      "type": "string",
      "errorMessage": { "type": "You must enter a string value (base error)." }
    },
    "field2": {
      "type": "object",
      "properties": {
        "deep": {
          "type": "number",
          "errorMessage": { "type": "I can't work with the value you provided (base error)." }
        },
        "deep2": {
          "type": "string"
        }
      }
    }
  },
  "required": ["field1"],
  "errorMessage": {
    "required": {
      "field1": "You must enter a value for field1 (base error)."
    }
  }
}
```

Within a given property (including the root object), you can define in context a map of failing rule segments and custom
error messages.  These custom error messages remain associated with the property when overriding schemas or reusing 
parts of a schema in a new schema.

The current `ajv-errors` implementation supports [templates](https://github.com/epoberezkin/ajv-errors#templates), which
may include references to the object being validated.  You cannot reference material from the schema itself, which 
limits the ability to define an error message once and reuse it as a variable in multiple templates.

Although the `ajv-errors` package does not currently have tests for complex reuse scenarios, in theory any inheritance
constructs supported by the language itself can be used to override individual inherited `errorMessages`, or to add new
`errorMessages`.

## Approach 2b: Our Own Custom Keyword

We can also define our own keyword(s) that are allowed in our variant of the JSON Schema language.  As an example, let's
add support for the same `errorMesssages` construct defined by `ajv-errors`.  There are two ways to make AJV aware of
our own custom keyword(s).


The first is to define our own metaschema.  A metaschema uses a version of the JSON Schema language to define what
keywords are allowed in writing schemas.  Unfortunately, with the current state of affairs, we would basically have to
fork the draft standard, and rewrite all the parts that use circular references.  The 
[metaschema snippet used by `ajv-error` to add the `errorMessages` construct](https://github.com/epoberezkin/ajv-errors/blob/master/index.js#L22)
might also be represented as a custom metaschema like the following:

```json
{
  "$schema": "custom-metaschema.json#",
  "$id": "custom-metaschema.json",
  "title": "Custom metaschema (extending draft v6)",
  "description": "Provides additional 'UI hints'...",
  "definitions": {
    "schemaArray": {
      "type": "array",
      "minItems": 1,
      "items": { "$ref": "#" }
    }
  },
  "properties": {
    "/": { "$ref": "http://json-schema.org/draft-06/schema#" },
    "errorMessages": {
      "type": ["string", "object"],
      "properties": {
        "properties": {"$ref": "#/definitions/stringMap"},
        "items": {"$ref": "#/definitions/stringList"},
        "required": {"$ref": "#/definitions/stringOrMap"},
        "dependencies": {"$ref": "#/definitions/stringOrMap"}
      },
      "additionalProperties": {"type": "string"},
      "definitions": {
        "stringMap": {
          "type": ["object"],
          "additionalProperties": {"type": "string"}
        },
        "stringOrMap": {
          "type": ["string", "object"],
          "additionalProperties": {"type": "string"}
        },
        "stringList": {
          "type": ["array"],
          "items": {"type": "string"}
        }
      }
    },
    "additionalItems": { "$ref": "#" },
    "items": {
      "anyOf": [
        { "$ref": "#" },
        { "$ref": "#/definitions/schemaArray" }
      ],
      "default": {}
    },
    "contains": { "$ref": "#" },
    "additionalProperties": { "$ref": "#" },
    "definitions": {
      "type": "object",
      "additionalProperties": { "$ref": "#" },
      "default": {}
    },
    "properties": {
      "type": "object",
      "additionalProperties": { "$ref": "#" },
      "default": {}
    },
    "patternProperties": {
      "type": "object",
      "additionalProperties": { "$ref": "#" },
      "default": {}
    },
    "dependencies": {
      "type": "object",
      "additionalProperties": {
        "anyOf": [
          { "$ref": "#" },
          { "$ref": "http://json-schema.org/draft-06/schema#/definitions/stringArray" }
        ]
      }
    },
    "propertyNames": { "$ref": "#" },
    "not": { "$ref": "#" }
  },
  "allOf": { "$ref": "#/definitions/schemaArray" },
  "anyOf": { "$ref": "#/definitions/schemaArray" },
  "oneOf": { "$ref": "#/definitions/schemaArray" },
  "default": {}
}
```
In summary, the above extends the draft v6 schema, but replaces all of its circular references (`$ref` values of `#`)
with ones that include our custom `errorMessages` keyword.  Once we have a custom metaschema, we would need to 
[make AJV aware of it](https://github.com/epoberezkin/ajv#addmetaschemaarrayobjectobject-schema--string-key)
before we can load our schemas or validate any content.  Although AJV has the best support for metaschemas, defining our
own metaschema is at least in theory something we can more reasonably expect other validators will eventually support.
Another key advantage is that our schemas could clearly indicate in their top-level `$schema` value that they are using 
a custom language, and not the unaltered core JSON Schema language.

The second approach (which `ajv-errors` itself uses) is to tell AJV that we have [a new keyword which is allowed for any property](https://github.com/epoberezkin/ajv#defining-custom-keywords).
This avoids our having to write and maintain a (recursive) custom metaschema that reuses material from the latest draft
metaschema.  Given that the default metaschemas allow [additional properties](https://spacetelescope.github.io/understanding-json-schema/reference/object.html#properties), 
our schemas would even validate.  However, their `$schema` variable would be somewhat misleading, in that it does not
describe our language additions or give any guidance as to acceptable values for our keywords.

In both cases, our schemas would look the same as the `ajv-errors` example above.  As we will discuss below, a key
advantage of either of these approaches is that we are not limited to what `ajv-errors` provides.  We can support 
multiple types of UI hints, nest them within a combined structure, or whatever makes the most sense to us.

# Internationalisation

Whatever route we choose, we need some means of replacing messages according to the locale.  We must also consider how
[reuse and inheritance]({filename}reusing-and-extending.md) affect i18n messages.

## Message Keys and Lookup

The first solution is to store message keys as the values in the right side of the above example, as in this 
snippet:

```json
{
  "errorMessages": {
    "#/properties/required/0": "my.message.bundle.enter.string",
    "#/properties/field1/type": "my.message.bundle.enter.string",
    "#/properties/deep/properties/required/0": "my.message.bundle.enter.number",
    "#/properties/deep/properties/field2/type": "my.message.bundle.enter.number"
  }
}
```
We would then have a default message bundle, and one for each supported language.  Depending on the user's locale,
we would display different text instead of the message key.  There might optionally be templating involved, as described
in [GPII-2444](https://issues.gpii.net/browse/GPII-2444).

This requires additional work when rendering content, as we are not simply retrieving a string value from the schema.
It also makes the schemas somewhat less readable for developers and integrators, as they cannot directly see the
text in context.


## Schema Overlays

In this approach, we embed the default language in the "core" schema, and "overlay" alternate wordings in
language-specific schemas.  Just for the sake of simplicity, I'll assume we're working with the same `errorMessages`
construct outlined in previous examples.  Let's assume we want to replace the error messages in the following example:

```json
{
  "$schema": "http://json-schema.org/schema#",
  "$id": "my-base-schema.json",
  "properties": {
    "field1": {
      "$id": "/field1",
      "type": "string",
      "errorMessage": { "type": "You must enter a string value (base error)." }
    }
  },
  "required": ["field1"],
  "errorMessage": {
    "required": {
      "field1": "You must enter a value for field1 (base error)."
    }
  }
}
```

Although you might want to merge in replacement keys with the "Message Keys and Lookup" strategy, the viability of the
"Schema Overlays" approach depends heavily on the ability to merge content.  One way to accomplish this is by using the
custom `$merge` and `$patch` keywords provided by [ajv-merge-patch](https://github.com/epoberezkin/ajv-merge-patch),
which add support for the mechanisms outlined in the RFCs for [JSON Merge Patch](https://tools.ietf.org/html/rfc7396) and
[JSON Patch](https://tools.ietf.org/html/rfc6902).  With that, we could prepare an "overlay" like the following:


```json

{
  "$schema": "http://json-schema.org/schema#",
  "$id": "my-base-schema-LOCALE.json",
  "$patch": {
    "source": { "$ref": "my-base-schema.json" },
    "with": [
      {
        "op": "replace",
        "path": "/properties/field1/errorMessage",
        "value": { "type": "replacement field message for LOCALE." }
      },
      {
        "op": "replace",
        "path": "/errorMessage/required/field1",
        "value": { "type": "replacement required message for LOCALE." }
      }
    ]
  }
}
```

This approach also assumes that we have some convention for looking up the locale-specific schema, for example, suffixing the core
schema with a language code.

## "Hybrid" Approach

It should also be possible to follow the first "Message Keys" approach, and use a utility to generate "patched" schemas
for each known locale.