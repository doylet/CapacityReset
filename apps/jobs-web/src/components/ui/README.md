# UI Component Library

A comprehensive set of reusable UI components built with **Headless UI** and **Tailwind CSS**.

All components are built on top of Headless UI primitives for:
- ✅ Full accessibility (ARIA, keyboard navigation, focus management)
- ✅ Better UX with proper state management
- ✅ Polymorphic rendering where applicable
- ✅ Framework-agnostic styling

## Components

### Button
Full-featured button component with multiple variants and states. Built on `@headlessui/react Button`.

**Variants:** `primary` | `secondary` | `outline` | `ghost` | `danger` | `success`  
**Sizes:** `sm` | `md` | `lg`

```tsx
import { Button } from '@/components/ui';
import { Save } from 'lucide-react';

// Basic usage
<Button>Click me</Button>

// With variants
<Button variant="primary">Primary</Button>
<Button variant="danger">Delete</Button>
<Button variant="outline">Cancel</Button>

// With icons
<Button leftIcon={<Save className="w-4 h-4" />}>Save</Button>
<Button rightIcon={<ArrowRight />}>Next</Button>

// Loading state
<Button loading>Saving...</Button>

// Polymorphic rendering
<Button as="a" href="/page">Link Button</Button>

// Full width
<Button fullWidth>Submit</Button>

// Different sizes
<Button size="sm">Small</Button>
<Button size="lg">Large</Button>
```

### Card
Flexible card container with header, body, and footer sections.

**Variants:** `default` | `bordered` | `elevated` | `flat`  
**Padding:** `none` | `sm` | `md` | `lg`

```tsx
import { Card, CardHeader, CardBody, CardFooter } from '@/components/ui';

<Card variant="elevated" padding="lg">
  <CardHeader 
    title="Card Title" 
    description="Card description"
  />
  <CardBody>
    Content goes here
  </CardBody>
  <CardFooter>
    <Button>Action</Button>
  </CardFooter>
</Card>

// Hoverable card
<Card hoverable>
  Interactive content
</Card>
```

### Input
Text input with labels, icons, and validation. Built on `@headlessui/react Input`.

**Variants:** `default` | `filled` | `flushed`  
**Sizes:** `sm` | `md` | `lg`

```tsx
import { Input } from '@/components/ui';
import { Search, Mail } from 'lucide-react';

// Basic input
<Input 
  label="Email" 
  placeholder="Enter your email"
  helperText="We'll never share your email"
/>

// With icons
<Input 
  leftIcon={<Search className="w-4 h-4" />}
  placeholder="Search..."
/>

<Input 
  rightIcon={<Mail className="w-4 h-4" />}
  placeholder="Email address"
/>

// With error
<Input 
  label="Password"
  type="password"
  error="Password is required"
/>

// Variants
<Input variant="filled" placeholder="Filled input" />
<Input variant="flushed" placeholder="Flushed input" />

// Full width
<Input fullWidth placeholder="Full width input" />
```

### Select
Dropdown select with custom styling. Built on `@headlessui/react Listbox` for better UX than native select.

**Variants:** `default` | `filled`  
**Sizes:** `sm` | `md` | `lg`

```tsx
import { Select } from '@/components/ui';

const options = [
  { value: '1', label: 'Option 1' },
  { value: '2', label: 'Option 2' },
  { value: '3', label: 'Option 3', disabled: true },
];

<Select 
  options={options}
  value={selectedValue}
  onChange={setSelectedValue}
  label="Choose an option"
  helperText="Select your preferred option"
/>

// With error
<Select 
  options={options}
  value={selectedValue}
  onChange={setSelectedValue}
  label="Country"
  error="Please select a country"
/>

// Full width
<Select 
  options={options}
  value={selectedValue}
  onChange={setSelectedValue}
  fullWidth
  placeholder="Choose..."
/>
```

**Note:** This component uses a controlled API with `options` array instead of children.

### Textarea
Multi-line text input. Built on `@headlessui/react Textarea`.

**Variants:** `default` | `filled`  
**Sizes:** `sm` | `md` | `lg`  
**Resize:** `none` | `vertical` | `horizontal` | `both`

```tsx
import { Textarea } from '@/components/ui';

<Textarea 
  label="Description"
  placeholder="Enter description"
  rows={4}
  helperText="Maximum 500 characters"
/>

// With error
<Textarea 
  label="Comments"
  error="Comments are required"
/>

// No resize
<Textarea resize="none" placeholder="Fixed size" />
```

### Badge
Small status indicators and labels.

**Variants:** `default` | `primary` | `secondary` | `success` | `warning` | `danger` | `info`  
**Sizes:** `sm` | `md` | `lg`

```tsx
import { Badge } from '@/components/ui';

// Basic badge
<Badge>Default</Badge>
<Badge variant="success">Active</Badge>
<Badge variant="danger">Critical</Badge>

// With dot indicator
<Badge variant="success" dot>Online</Badge>

// Removable
<Badge 
  variant="primary" 
  removable 
  onRemove={() => console.log('removed')}
>
  Tag
</Badge>

// Different sizes
<Badge size="sm">Small</Badge>
<Badge size="lg">Large</Badge>
```

### Spinner
Loading indicators.

**Variants:** `primary` | `secondary` | `white`  
**Sizes:** `xs` | `sm` | `md` | `lg` | `xl`

```tsx
import { Spinner } from '@/components/ui';

// Basic spinner
<Spinner />

// With label
<Spinner label="Loading data..." />

// Different variants
<Spinner variant="primary" />
<Spinner variant="white" /> // For dark backgrounds

// Different sizes
<Spinner size="xs" />
<Spinner size="xl" />
```

### Alert
Feedback messages for users. Built with `@headlessui/react Description`.

**Variants:** `info` | `success` | `warning` | `error`

```tsx
import { Alert } from '@/components/ui';

// Basic alert
<Alert variant="info">
  This is an informational message
</Alert>

// With title
<Alert 
  variant="success" 
  title="Success!"
>
  Your changes have been saved
</Alert>

// Closable
<Alert 
  variant="warning"
  closable
  onClose={() => console.log('closed')}
>
  This is a warning message
</Alert>

// Custom icon
<Alert 
  variant="error"
  icon={<CustomIcon />}
  title="Error"
>
  Something went wrong
</Alert>
```

### Switch
Toggle switch component. Built on `@headlessui/react Switch`.

**Variants:** `primary` | `success` | `danger`  
**Sizes:** `sm` | `md` | `lg`

```tsx
import { Switch } from '@/components/ui';

const [enabled, setEnabled] = useState(false);

// Basic switch
<Switch checked={enabled} onChange={setEnabled} />

// With label
<Switch 
  checked={enabled} 
  onChange={setEnabled}
  label="Enable notifications"
  description="Receive email notifications for updates"
/>

// Different variants
<Switch checked={enabled} onChange={setEnabled} variant="success" />
<Switch checked={enabled} onChange={setEnabled} variant="danger" />

// Different sizes
<Switch checked={enabled} onChange={setEnabled} size="sm" />
<Switch checked={enabled} onChange={setEnabled} size="lg" />
```

### Checkbox
Checkbox component with optional label and description. Built on `@headlessui/react Checkbox`.

**Variants:** `primary` | `success` | `danger`  
**Sizes:** `sm` | `md` | `lg`

```tsx
import { Checkbox } from '@/components/ui';

const [checked, setChecked] = useState(false);

// Basic checkbox
<Checkbox checked={checked} onChange={setChecked} />

// With label
<Checkbox 
  checked={checked} 
  onChange={setChecked}
  label="Accept terms and conditions"
  description="You must accept the terms to continue"
/>

// Different variants
<Checkbox checked={checked} onChange={setChecked} variant="success" />
<Checkbox checked={checked} onChange={setChecked} variant="danger" />

// Indeterminate state
<Checkbox 
  checked={checked} 
  onChange={setChecked}
  indeterminate={true}
/>
```

### Radio
Radio group component. Built on `@headlessui/react RadioGroup`.

**Variants:** `primary` | `success` | `danger`  
**Sizes:** `sm` | `md` | `lg`  
**Orientation:** `vertical` | `horizontal`

```tsx
import { Radio } from '@/components/ui';

const [selected, setSelected] = useState('1');

const options = [
  { value: '1', label: 'Option 1', description: 'Description for option 1' },
  { value: '2', label: 'Option 2' },
  { value: '3', label: 'Option 3', disabled: true },
];

// Basic radio group
<Radio 
  value={selected}
  onChange={setSelected}
  options={options}
/>

// With label
<Radio 
  value={selected}
  onChange={setSelected}
  options={options}
  label="Choose an option"
/>

// Horizontal orientation
<Radio 
  value={selected}
  onChange={setSelected}
  options={options}
  orientation="horizontal"
/>

// Different variants
<Radio 
  value={selected}
  onChange={setSelected}
  options={options}
  variant="success"
/>
```

## Headless UI Integration

All form components now use Headless UI primitives:

- **Button** → `@headlessui/react Button`
- **Input** → `@headlessui/react Input`
- **Textarea** → `@headlessui/react Textarea`
- **Select** → `@headlessui/react Listbox` (enhanced UX)
- **Switch** → `@headlessui/react Switch`
- **Checkbox** → `@headlessui/react Checkbox`
- **Radio** → `@headlessui/react RadioGroup`
- **Alert** → `@headlessui/react Description`

This provides:
- Automatic accessibility (ARIA attributes, roles)
- Keyboard navigation
- Focus management
- Screen reader support
- Proper state handling

## Design System

### Colors
- **Primary:** Blue (`blue-600`)
- **Secondary:** Gray (`gray-600`)
- **Success:** Green (`green-600`)
- **Warning:** Yellow (`yellow-600`)
- **Danger:** Red (`red-600`)
- **Info:** Cyan (`cyan-600`)

### Sizes
- **sm:** Small (compact UI)
- **md:** Medium (default)
- **lg:** Large (prominent UI)

### Common Props

Most components support:
- `className` - Additional CSS classes
- `disabled` - Disable the component
- `fullWidth` - Stretch to full container width
- Standard HTML attributes for the underlying element

## Accessibility

All components are built with accessibility in mind:
- Semantic HTML elements
- Proper ARIA attributes
- Keyboard navigation support
- Focus management with visible focus rings
- Screen reader support

## TypeScript

All components are fully typed with TypeScript. Import types:

```tsx
import type { ButtonProps, ButtonVariant } from '@/components/ui';
```

## Customization

Components accept `className` prop for additional styling:

```tsx
<Button className="my-custom-class">
  Custom styled button
</Button>
```

All components use Tailwind's utility classes, making them easy to customize in your design system.
