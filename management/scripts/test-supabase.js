const { createClient } = require('@supabase/supabase-js');

const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL;
const supabaseKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY;

console.log('Testing Supabase connection...');
console.log('URL:', supabaseUrl);
console.log('Key:', supabaseKey ? `${supabaseKey.substring(0, 20)}...` : 'MISSING');

const supabase = createClient(supabaseUrl, supabaseKey);

async function testConnection() {
  try {
    // Test 1: Check if we can connect
    const { data: users, error } = await supabase
      .from('users')
      .select('name, surname, role')
      .limit(5);

    if (error) {
      console.error('❌ Supabase error:', error);
      return;
    }

    console.log('✅ Connected to Supabase!');
    console.log('📊 Found', users?.length || 0, 'users');

    if (users && users.length > 0) {
      console.log('\nUsers in database:');
      users.forEach(u => {
        console.log(`  - ${u.name} ${u.surname} (${u.role})`);
      });

      const pms = users.filter(u => u.role === 'project_manager');
      console.log(`\n✨ Project Managers: ${pms.length}`);
    }
  } catch (err) {
    console.error('❌ Connection failed:', err.message);
  }
}

testConnection();
